import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/memory/src"
P = "java/workbench/memory/l04"
K = "kotlin/workbench/memory/l04"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :memory:demo -Pmain=workbench.memory.l04."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


# a 8 x 3 grid of regions plus a legend
GRID = [
    ["E", "E", "E", "S", "O", "O", ".", "E"],
    ["O", "G", "H", "h", "h", "E", ".", "O"],
    [".", "O", "E", "G", "O", ".", "S", "G"],
]
CLS = {"E": "box-ok", "S": "box-a", "O": "box", "G": "box-bad", "H": "box-b", "h": "box-b", ".": "box-dim"}
cells = []
for r, row in enumerate(GRID):
    for c, k in enumerate(row):
        x, y = 20 + c * 62, 40 + r * 54
        if k == "h":
            continue
        w = 56 if k != "H" else 56 + 62 * 2          # the humongous object spans three regions
        cells.append(f'<rect class="{CLS[k]}" x="{x}" y="{y}" width="{w}" height="46" rx="8"/>')
        label = {"G": "O", ".": ""}.get(k, k)
        if k == "H":
            label = "H: one 3 MiB array"
        if label:
            cells.append(f'<text class="{"t" if k != "H" else "t-s"}" x="{x + w / 2:.0f}" y="{y + 28}" text-anchor="middle">{label}</text>')
legend = [("box-ok", "E: eden"), ("box-a", "S: survivor"), ("box", "O: old"), ("box-bad", "O: mostly garbage"), ("box-b", "H: humongous"), ("box-dim", "free")]
leg = []
for i, (cls, txt) in enumerate(legend):
    y = 40 + i * 27
    leg.append(f'<rect class="{cls}" x="530" y="{y}" width="140" height="22" rx="8"/>')
    leg.append(f'<text class="t-s" x="600" y="{y + 15}" text-anchor="middle">{txt}</text>')
FIGURE = ('<svg viewBox="0 0 690 290" role="img" aria-label="A G1 heap as a grid of equal regions marked eden, survivor, old, mostly-garbage old, humongous and free. '
          'A young pause evacuates all eden and survivor regions; a mixed pause also evacuates the old regions with the most garbage">'
          '<text class="t t-m" x="262" y="24" text-anchor="middle">one G1 heap: equal regions, each with a role for now</text>'
          + "".join(cells) + "".join(leg) +
          '<text class="t-s" x="262" y="226" text-anchor="middle">young pause: copy the live objects out of every E and S region</text>'
          '<text class="t-s" x="262" y="248" text-anchor="middle">mixed pause: the same, plus a few O regions with the most garbage</text>'
          '<text class="t-s" x="262" y="270" text-anchor="middle">emptied regions become free; any region can take any role next</text>'
          '</svg>')

S1 = """A payment request allocates the parsed JSON, a few DTOs, some strings and the response, and all of it is garbage a few milliseconds later. A few objects live much longer: a cached merchant config, a pooled connection, the entries of an idempotency cache. That split has a name, the **weak generational hypothesis**: most objects die young. A real log shows how lopsided it is. In one generational ZGC minor collection on a test workload, eden held 27 MB of live objects and 470 MB of garbage.

HotSpot's collectors split the heap to match. New objects go into eden, in the **young generation**. When eden fills, a **young collection** finds the few live objects there and copies them into a survivor space. Everything else in eden is reclaimed at once, and the collector never even looks at it. Each time an object survives, its age goes up by one; it lives in the 4 age bits of the mark word from lesson 1. After enough survivals (at most 15, set by `MaxTenuringThreshold`, and G1 lowers it when survivor space runs short), the object is **promoted** to the **old generation**, which is collected much less often.

The payoff is that a young collection costs time in proportion to what survives, not to what was allocated. A 500 MB eden with 5 MB of survivors gives a short pause. The same eden with 200 MB of survivors, for example a large batch held in memory while it's processed, gives a long one, and those objects then fill the old generation too.

That makes medium-lived objects the expensive kind. They survive a few young collections, get copied each time, get promoted, and then die in the old generation, where only a bigger collection can reclaim them. An idempotency cache with a 10-minute expiry is exactly that shape."""

S2 = """A garbage collector needs two steps to be correct, and you can write both in a few lines. Here's a toy one. Its heap is a map from an object id to the ids that object's fields point to:

```java
Set<Integer> mark(Collection<Integer> roots) {
    Set<Integer> live = new HashSet<>();
    for (int root : roots) visit(root, live);
    return live;
}

void visit(int id, Set<Integer> live) {
    if (!live.add(id)) return;                        // already marked: this also ends cycles
    for (int next : refs.get(id)) visit(next, live);  // follow every reference field
}

Set<Integer> sweep(Set<Integer> live) {
    Set<Integer> dead = new HashSet<>(refs.keySet());
    dead.removeAll(live);
    refs.keySet().removeAll(dead);                    // their memory is free again
    return dead;
}
```

```kotlin
fun mark(roots: Collection<Int>): Set<Int> {
    val live = HashSet<Int>()
    fun visit(id: Int) {
        if (!live.add(id)) return                     // already marked: this also ends cycles
        refs.getValue(id).forEach(::visit)            // follow every reference field
    }
    roots.forEach(::visit)
    return live
}

fun sweep(live: Set<Int>): Set<Int> {
    val dead = refs.keys.filterTo(HashSet()) { it !in live }
    refs.keys.removeAll(dead)                         // their memory is free again
    return dead
}
```

**Marking** follows references from the roots and remembers every object it reaches. **Sweeping** frees the rest. Two things follow from the code. A cycle of objects that point at each other, with no root pointing in, gets freed: a tracing collector asks only whether a root can reach an object, never how many references it has. And the sweep visits every object, dead or alive, so its cost grows with the heap. (The recursion is a toy shortcut: a chain of 200,000 objects overflows a thread's stack. A real collector keeps its own mark stack, and so will your lab.)

HotSpot replaces the sweep with better moves. **Copying**, also called evacuation, moves the live objects into empty space and then treats the whole old space as free. It never touches the dead objects, so its cost follows the live ones, and it compacts memory as a side effect. **Mark-compact** slides the live objects together inside the space they're in: no spare room needed, but several passes. Young collections copy, which is why G1 calls them evacuation pauses. G1's full GC is a mark-compact of the whole heap, the last resort.

Moving an object is only safe while no thread is using it. So these steps run in a **stop-the-world pause** at a **safepoint**: a moment when every application thread is stopped at a known place, with its references where the collector can find and update them. Compiled code checks for a pending safepoint at method returns and in loops. Getting every thread there takes time of its own, and `-Xlog:safepoint` splits it out:

```text
Safepoint "G1CollectForAllocation", Time since last: 32350666 ns, Reaching safepoint: 3409 ns,
Cleanup: 4274 ns, At safepoint: 1671830 ns, Leaving safepoint: 1364 ns, Total: 1680877 ns
```

"Reaching safepoint" (3.4 microseconds here) is how long the slowest thread took to stop. "At safepoint" (1.67 ms) is the collector's work. When the first number is large, the collector is not your problem: some thread ran a long time without reaching a safepoint check."""

S3 = """There's a catch in the young collection story. To decide which young objects are alive, the collector follows references from the roots. But old objects point at young ones all the time: the idempotency cache sitting in the old generation gets a new young entry with every request. If a young collection had to scan the whole old generation to find those pointers, it would cost as much as a full GC.

The fix is to do the bookkeeping when the pointer is written. The heap is divided into **cards** of 512 bytes (G1 prints `CardTable entry size: 512` at startup), and the **card table** has one byte per card. Every time your code stores a reference into a field, it also runs a few extra instructions, the **write barrier**, that mark the card holding that field as dirty:

```text
cache.entries[i] = newEntry;                   // the store you wrote
card_table[address_of(field) >> 9] = DIRTY;    // what the barrier adds (512 = 2^9)
```

A young collection then scans the roots plus the dirty cards, not the whole old generation. G1 goes a step further: each region keeps a **remembered set**, the cards elsewhere in the heap that point into that region. "Merge Heap Roots" in G1's pause log is the step that folds those remembered sets into the roots for the pause.

G1 has a second barrier for its concurrent marking, which section 5 describes. While the application keeps running during marking, it can move a reference out of an object the marker hasn't visited into one it already has. To catch that, the barrier records the old value before a reference is overwritten, so the marker still finds every object that was live when marking began. The technique is called snapshot-at-the-beginning (SATB), and the comment on G1's barrier class in the JDK 25 source calls it "a logging barrier to support snapshot-at-the-beginning marking".

These barriers are the steady cost of a generational, concurrent collector: a few instructions on every reference store in your code, all the time. Lesson 5 shows that ZGC pays at reference loads instead.

Reason it through before you move on. A Kafka consumer keeps a long-lived map of the last offset per partition, so the map sits in the old generation. For every record it replaces one partition's value with a new boxed `Long`. Which cards does the barrier dirty, and what does the next young pause scan? (Only the few cards holding the map entries whose value changed. The pause scans those cards and the roots, finds the new `Long`s, and never reads the rest of the old generation.)"""

S4 = """G1, the default collector, doesn't keep one big eden and one big old space. It cuts the heap into equal **regions**, and each region has a role for a while: eden, survivor, old, humongous or free. The roles move around. After a young pause, the evacuated eden regions are free, and next time any of them can become anything.

The region size comes from the max heap. In the JDK 25 source it's the max heap divided by 2048, clamped between 1 MB and 32 MB, then rounded up to a power of two. A 1 GB heap gets 1 MB regions, the 3.4 GB default heap on a 13 GB machine got 2 MB, and `-Xmx40g` gets 32 MB.

Regions explain one of G1's sharp edges. An object larger than half a region is **humongous**. It skips TLABs and eden and gets its own run of whole, contiguous regions, which count as old from the start. A 3 MiB `byte[]` is 3 MiB plus a 16-byte header, so with 1 MB regions it takes four regions, and nearly all of the fourth one is wasted. A burst of humongous allocations can start a concurrent cycle on its own (the log says `G1 Humongous Allocation`), and each one needs enough free regions in a row. G1 does reclaim dead humongous objects early: in the demo, the first young pause freed `Humongous regions: 12->0`.

In payment services the humongous objects are usually whole payloads held in one array: a settlement file, a large JSON response, a PDF statement. If your log is full of `G1 Humongous Allocation`, stream those payloads instead of buffering them, or raise the region size with `-XX:G1HeapRegionSize` until they are under half a region."""

S5 = """Most of the time G1 runs only young pauses. Each one evacuates all eden and survivor regions. In `Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 12.723ms`, 14 MB was in use before, 1 MB after, the committed heap is 256 MB, and the stop-the-world pause took 12.7 ms.

The old regions fill up slowly with promoted objects. When old-generation occupancy crosses the initiating heap occupancy percent (IHOP: 45% to begin with, then adapted from what G1 observes), G1 starts a **concurrent marking cycle**. Here's one from a 1 GB heap, verbatim:

```text
GC(20) Pause Young (Concurrent Start) (G1 Humongous Allocation) 556M->527M(1024M) 13.734ms
GC(21) Concurrent Mark Cycle
GC(21) Pause Remark 583M->583M(1024M) 0.835ms
GC(21) Pause Cleanup 637M->637M(1024M) 0.379ms
GC(21) Concurrent Mark Cycle 53.866ms
GC(22) Pause Young (Prepare Mixed) (G1 Evacuation Pause) (Evacuation Failure) 996M->760M(1024M) 43.391ms
GC(23) Pause Young (Mixed) (G1 Evacuation Pause) 981M->660M(1024M) 10.429ms
```

The cycle starts inside a young pause (`Concurrent Start`). Marking then runs on a background thread for 54 ms while the application keeps working, with two short pauses to finish (`Remark`, `Cleanup`). Now G1 knows how much of each old region is live. The next young pause (`Prepare Mixed`) is the last young-only one. Then come the **mixed** pauses: all young regions plus a few old ones, the ones with the most garbage. That choice is where the name Garbage First comes from.

Which old regions? From the JDK 25 source: only regions less than 85% live are candidates (`G1MixedGCLiveThresholdPercent`). G1 sorts them by efficiency, best first. It drops the cheapest ones as long as the garbage it leaves behind stays within 5% of the heap (`G1HeapWastePercent`). And each mixed pause takes at least an eighth of the candidates, so the work is done in at most 8 mixed pauses (`G1MixedGCCountTarget`). The lab has you write these rules.

Two phrases in the log mean trouble. `(Evacuation Failure)` means G1 ran out of free regions to copy into and had to leave objects where they were. `Pause Full (G1 Compaction Pause)` is the fallback: the whole heap, mark-compact, everything stopped. Both say the heap is too small for the live data plus the allocation rate, and the 200 ms pause goal (`MaxGCPauseMillis`) can't fix that."""

L = {
 "id": "mem-04",
 "title": "How garbage collectors work: generations and G1",
 "minutes": 38,
 "goal": "By the end you can explain generations, copying and safepoints, say what write barriers and card tables are for, and read G1's young, concurrent and mixed collections in a real log.",
 "warmup": {
  "q": "Two young collections each start with a full 500 MB eden. In the first, 5 MB of objects survive. In the second, 200 MB survive. Which pause is longer?",
  "options": ["They take about the same time, because eden was the same size", "The first, because it frees more memory", "The second, because the collector copies every surviving object", "Neither: young collections don't pause the application"],
  "answer": 2,
  "why": "A young collection copies the live objects out of eden and frees the rest in one go, so its cost follows the survivors, not the garbage. 200 MB of survivors is forty times the copying work. In G1, Serial and Parallel, young collections are stop-the-world pauses."
 },
 "sections": [
  {
   "h": "Most objects die young, so the heap has generations",
   "body": S1,
   "try": {
    "title": "Watch survivors age",
    "minutes": 3,
    "steps": [
     "Read `GenerationsDemo`. It runs the lesson's service load (`ServiceLoad.java`: short-lived request garbage plus a growing cache) for one second, with G1's age table logged.",
     "Run it. For each `Pause Young` line, compare the heap before and after the arrow.",
     "Follow one number through the age table from GC(0) to GC(2)."
    ],
    "code": demo("GenerationsDemo"),
    "expect": "Each young pause frees most of what it found: `54M->4M` means about 50 of the 54 MB were garbage. The age table shows the survivors getting older: the 812 KB at age 1 in GC(0) appears at age 2 in GC(1) and at age 3 in GC(2). Those are cache entries, the long-lived objects. Exact numbers change from run to run."
   }
  },
  {
   "h": "Collectors mark, copy or compact, and they stop the world to move objects",
   "body": S2,
   "try": {
    "title": "Separate stopping from collecting",
    "minutes": 3,
    "steps": [
     "Run `SafepointDemo`. It logs every safepoint during one second of service load and prints the first five GC safepoints.",
     "For each line, compare \"Reaching safepoint\" with \"At safepoint\". Both are in nanoseconds."
    ],
    "code": demo("SafepointDemo"),
    "expect": "Reaching the safepoint takes a few thousand nanoseconds (a few microseconds), and the GC work at the safepoint takes one to five million (one to five milliseconds). The threads in this load stop quickly because their loops are short. A long \"Reaching safepoint\" would point at a thread that runs a long time between safepoint checks."
   }
  },
  {
   "h": "Write barriers and card tables keep a young collection small",
   "body": S3
  },
  {
   "h": "G1 splits the heap into regions",
   "body": S4,
   "figure": {"svg": FIGURE, "caption": "G1 gives each equal region a role. Young pauses evacuate every eden and survivor region; mixed pauses also take the old regions with the most garbage."},
   "try": {
    "title": "Count the regions of a humongous object",
    "minutes": 3,
    "steps": [
     "Read `HumongousDemo`. It runs a 1 GB G1 heap, so regions are 1 MB, and allocates 3 MiB arrays with ordinary garbage in between.",
     "Predict how many regions each 3 MiB array takes, then run it."
    ],
    "code": demo("HumongousDemo"),
    "expect": "`Heap Region Size: 1M`, then the first young pause reports `Humongous regions: 12->0`. Twelve regions held three arrays, four regions each, because 3 MiB plus a 16-byte header doesn't fit in three. All three were already dead, so the young pause reclaimed them right away."
   },
   "refs": [
    {"title": "g1HeapRegion.cpp at jdk-25-ga: how G1 picks the region size", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1HeapRegion.cpp", "kind": "read"}
   ]
  },
  {
   "h": "G1's cycle: young pauses, concurrent marking, mixed collections",
   "body": S5,
   "try": {
    "title": "Squeeze G1 until it struggles",
    "minutes": 4,
    "steps": [
     "Read `G1CycleDemo`. It runs the service load for 3 seconds in a 256 MB heap, with the cache growing to 60% of it. It counts each kind of GC event and prints the first line of each kind, in the order they happened.",
     "Run it. Find the cycle from this section in the first lines: Concurrent Start, Remark, Cleanup, Prepare Mixed, Mixed.",
     "Run it again and compare the counts."
    ],
    "code": demo("G1CycleDemo"),
    "expect": "Dozens of concurrent cycles, each with a Remark and a Cleanup, more than a hundred mixed pauses, and a large number of evacuation failures. Most runs also show one or more `Pause Full (G1 Compaction Pause)`. The counts change on every run. This heap is too small for its live data on purpose: it is the \"bad config\" you want to recognize in your own logs."
   },
   "refs": [
    {"title": "g1CollectionSetChooser.cpp at jdk-25-ga: choosing mixed-collection candidates", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1CollectionSetChooser.cpp", "kind": "read"}
   ]
  }
 ],
 "analogy": "G1 runs a warehouse of identical storage bays. New stock lands in the receiving bays. Every so often a crew moves the few boxes still wanted from receiving into long-term bays, then declares every receiving bay empty at once: that's a young pause. Now and then an inspector walks the long-term bays while work goes on and notes how full each one is: concurrent marking. Then the crew empties the emptiest long-term bays first, a few per shift, because they give back the most space for the least lifting: mixed pauses. A pallet too big for one bay gets several neighbouring bays to itself: a humongous object. Where it breaks: a real crew can move boxes while people work around them. G1 has to stop every thread before it moves anything, and that stop is your pause.",
 "in_your_world": "A Quarkus payment API in a container with a 1 GiB memory limit gets a 256 MB heap by default, and so 1 MB regions. Any payload over 512 KB held in one array is humongous there: a big merchant's settlement CSV, a base64 PDF statement inside a JSON response, a Kafka batch read into one buffer. And the idempotency cache, whose entries live for minutes, is the classic medium-lived structure: each entry survives several young pauses, gets promoted, and has to wait for marking and mixed collections to be freed. When the after-values of young pauses keep rising and you see `(Evacuation Failure)`, the heap is too small for that cache, or the cache has no bound (lesson 7).",
 "mistake": "Lowering `-XX:MaxGCPauseMillis` to get rid of `(Evacuation Failure)` and `Pause Full (G1 Compaction Pause)`. The pause goal only steers how much work G1 plans per pause: how big eden gets and how many old regions a mixed pause takes. It can't create free regions. Evacuation failures and full GCs mean the live data plus the allocation rate don't fit, and a smaller goal usually means more, smaller pauses on the same full heap. Read the after-values of the young pauses to find the live set, then give the heap room for it, bound or shrink what's live, and stream payloads that would be humongous.",
 "compare": {
  "title": "Buffer a settlement file, or stream it",
  "java": {"title": "SettlementImport.java", "src": "// buffers the whole 3 MB file: a humongous byte[] while reading, then a humongous String\nString csv = Files.readString(file);\nfor (String line : csv.split(\"\\n\")) settle(line);\n\n// streams it: one line at a time, only small objects\ntry (Stream<String> lines = Files.lines(file)) {\n    lines.forEach(this::settle);\n}"},
  "kotlin": {"title": "SettlementImport.kt", "src": "// buffers the whole 3 MB file: a humongous byte[] while reading, then a humongous String\nval csv = file.readText()                       // kotlin.io.path.readText on a Path\ncsv.split(\"\\n\").forEach(::settle)\n\n// streams it: one line at a time, only small objects\nfile.useLines { lines -> lines.forEach(::settle) }"},
  "note": "The GC sees the same thing from both languages: the buffered version creates objects of several megabytes, which are humongous on any heap with regions of 4 MB or less, and the streaming version never holds more than a line. The difference is only in the API. Java's `Files.lines` returns a `Stream` you must close yourself, so it goes in try-with-resources. Kotlin's `Path.useLines` opens the reader, hands you a `Sequence`, and closes it when the block ends."
 },
 "worked": {
  "title": "Read a struggling G1 log",
  "steps": [
   {"say": "A service has a 256 MB heap. These are the first lines of its `-Xlog:gc` output (verbatim from a test run). Before you read on, look at the number after each arrow.",
    "code": "GC(0) Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 1.641ms\nGC(1) Pause Young (Normal) (G1 Evacuation Pause) 55M->4M(256M) 3.176ms\nGC(2) Pause Young (Normal) (G1 Evacuation Pause) 129M->11M(256M) 8.132ms\nGC(4) Pause Young (Normal) (G1 Evacuation Pause) 168M->27M(256M) 11.684ms\nGC(8) Pause Young (Normal) (G1 Evacuation Pause) 195M->59M(256M) 8.157ms\nGC(12) Pause Young (Normal) (G1 Evacuation Pause) 228M->92M(256M) 7.601ms",
    "lang": "text"},
   {"say": "1. Read the floor. The after-values (1, 4, 11, 27, 59, 92 MB) are what's still live after each young pause, and they climb by about 8 MB every pause. Either the service is warming a cache, or something is leaking. Either way the old generation is filling.",
    "code": "", "lang": ""},
   {"say": "2. Find the turn. A few pauses later the heap is nearly full, copies start to fail, and G1 starts marking because of a humongous allocation.",
    "code": "GC(13) Pause Young (Normal) (G1 Evacuation Pause) (Evacuation Failure) 240M->162M(256M) 7.055ms\nGC(14) Pause Young (Concurrent Start) (G1 Humongous Allocation) 195M->164M(256M) 4.194ms\nGC(15) Concurrent Mark Cycle\nGC(15) Pause Remark 186M->185M(256M) 0.343ms\nGC(15) Pause Cleanup 197M->197M(256M) 0.110ms\nGC(17) Pause Young (Prepare Mixed) (G1 Evacuation Pause) 242M->176M(256M) 2.276ms\nGC(18) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure) 242M->195M(256M) 4.411ms",
    "lang": "text"},
   {"say": "3. Read the verdict. Mixed pauses can't win: they free 40 to 60 MB each, and the heap is back near 240 MB a few milliseconds later. Then comes the fallback. The full GC brings the heap down to 94 MB, and that number is the live set: 94 MB of real data in a 256 MB heap, with a high allocation rate on top.",
    "code": "GC(76) Pause Full (G1 Compaction Pause) 224M->94M(256M) 16.652ms",
    "lang": "text"},
   {"say": "4. Decide. G1 copies, so it needs free regions to copy into. As a rule of thumb (mine, not G1's), give G1 a heap of two to three times the live set, so about 300 MB here, and then confirm with a new log that evacuation failures and full GCs are gone. If the floor keeps climbing even then, it's a leak, not a sizing problem, and lesson 7 finds it.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A toy collector, then G1 by numbers",
  "minutes": 15,
  "files": [
   "labs/memory/src/main/kotlin/workbench/memory/l04/ToyHeap.kt",
   "labs/memory/src/main/kotlin/workbench/memory/l04/G1Model.kt",
   "labs/memory/src/main/kotlin/workbench/memory/l04/OldRegion.kt"
  ],
  "run": "./gradlew :memory:test --tests 'workbench.memory.l04.*'",
  "steps": [
   "Run the tests. Fourteen of fifteen fail; the one that passes tests a helper you're given.",
   "Start with the toy: write `ToyHeap.mark` without recursion. Keep an `ArrayDeque` of objects still to visit, pop one, mark it, push its references. Then write `sweep`. The `ToyHeapTest` tests should pass, including the unreachable cycle and the 200,000-object chain.",
   "Now G1. Write `regionSize`: divide by 2048, clamp to 1 MB to 32 MB, then round up to a power of two. In that order. Each KDoc gives the rule from the JDK 25 source.",
   "Write `isHumongous` (strictly more than half a region) and `regionsFor` (whole regions, rounded up).",
   "Write `mixedCandidates`: filter, sort, then prune from the end, using the given `minOldRegionsPerMixedGc`. Run the tests until all fifteen pass, then read the test for the 3 MiB settlement file and explain its numbers to yourself."
  ],
  "hints": [
   "In `mark`, skip an object that is already marked when you pop it. That one check ends cycles and avoids scanning anything twice.",
   "`(a + b - 1) / b` rounds a division up, for positive numbers.",
   "`coerceIn(MB, 32 * MB)` clamps. For the power of two, start at 1 MB and double until you reach the wanted size.",
   "`compareByDescending { regionBytes - it.liveBytes }.thenBy { it.index }` sorts the candidates.",
   "Pruning: walk back from the last candidate. Stop when you're down to the minimum, or when dropping the next one would push the total dropped garbage past 5% of the heap."
  ],
  "done_when": "All 15 tests in `ToyHeapTest` and `G1ModelTest` pass."
 },
 "drill": {
  "title": "Size G1's regions in your head",
  "minutes": 4,
  "prompt": "Close the page. For a max heap of 6 GB: what region size does G1 pick? Is a 2.5 MB JSON response humongous there? How many regions does it take? Then write `regionSize` from memory.",
  "answer": {
   "lang": "java",
   "src": "// 6 GB / 2048 = 3 MB, clamped (already between 1 and 32 MB), rounded up to a power of two: 4 MB regions.\n// Humongous means more than half a region: 2.5 MB > 2 MB, so yes. It takes 1 region (2.5 MB <= 4 MB).\nstatic long regionSize(long maxHeapBytes) {\n    long mb = 1024 * 1024;\n    long wanted = Math.clamp(maxHeapBytes / 2048, mb, 32 * mb);   // Math.clamp is JDK 21\n    long size = mb;\n    while (size < wanted) size *= 2;\n    return size;\n}",
   "alt": {
    "lang": "kotlin",
    "src": "// 6 GB / 2048 = 3 MB, clamped (already between 1 and 32 MB), rounded up to a power of two: 4 MB regions.\n// Humongous means more than half a region: 2.5 MB > 2 MB, so yes. It takes 1 region (2.5 MB <= 4 MB).\nfun regionSize(maxHeapBytes: Long): Long {\n    val mb = 1024L * 1024\n    val wanted = (maxHeapBytes / 2048).coerceIn(mb, 32 * mb)\n    var size = mb\n    while (size < wanted) size *= 2\n    return size\n}"
   }
  }
 },
 "recap": [
  "Most objects die young. A young collection copies the few survivors out of eden, so it costs what survives, not what was allocated.",
  "A collector marks what the roots can reach and frees the rest, so unreachable cycles go too. Copying costs what survives; moving objects needs a stop-the-world pause at a safepoint.",
  "Write barriers mark 512-byte cards dirty on every reference store, so a young collection scans dirty cards instead of the whole old generation. G1's SATB barrier keeps concurrent marking correct.",
  "G1 cuts the heap into regions of 1 to 32 MB. Objects over half a region are humongous: they take whole contiguous regions and count as old from the start.",
  "When old-generation occupancy crosses IHOP, G1 marks concurrently, then runs mixed pauses on old regions under 85% live, best first, in at most 8 pauses.",
  "`(Evacuation Failure)` and `Pause Full (G1 Compaction Pause)` mean the heap is too small for the live data and allocation rate. The pause goal can't fix that."
 ],
 "quiz": [
  {
   "q": "A service runs on a 2 GB heap with G1 and default settings. Which of these is a humongous allocation?",
   "options": ["`new byte[400_000]` for a receipt image", "A `HashMap` with 30,000 entries", "`new byte[700_000]` for a settlement file chunk", "A `String` of 300,000 Latin-1 characters"],
   "answer": 2,
   "why": "2 GB / 2048 is exactly 1 MB, so regions are 1 MB and the humongous threshold is 512 KB. 700,000 bytes is over it. 400,000 bytes and a 300,000-character Latin-1 string (a 300 KB array) are under it. A `HashMap` is many small objects; with 30,000 entries its table has 65,536 slots, a 256 KB array."
  },
  {
   "q": "Why does a young collection not have to scan the whole old generation for pointers into eden?",
   "options": [
    "Old objects are never allowed to point to young objects",
    "The write barrier marks dirty cards when references are stored, and the collector scans only those",
    "The JIT moves such objects into the old generation right away",
    "G1 copies the old generation in every young pause"
   ],
   "answer": 1,
   "why": "Old-to-young pointers are normal, for example a cache in the old generation getting new entries. Every reference store runs a barrier that marks the 512-byte card it wrote to as dirty. A young pause scans the roots plus the dirty cards; in G1, remembered sets track which cards point into which region."
  },
  {
   "q": "A G1 log shows `GC(42) Pause Young (Normal) (G1 Evacuation Pause) 1210M->1180M(1536M)`, then `(Evacuation Failure)` on the next pauses, then `Pause Full (G1 Compaction Pause) 1490M->1150M(1536M)`. What does it tell you?",
   "options": [
    "The pause goal is too high; set `-XX:MaxGCPauseMillis=50`",
    "About 1.15 GB is really live in a 1.5 GB heap, which leaves G1 too little room to copy",
    "The young generation is too small; the old generation is fine",
    "The application calls `System.gc()`"
   ],
   "answer": 1,
   "why": "The full GC's after-value is the live set: 1,150 MB of 1,536 MB. A young pause that frees only 30 MB, and copies that fail for lack of free regions, say the same thing. A smaller pause goal can't create free regions. A `System.gc()` call would show `(System.gc())` as the cause."
  },
  {
   "q": "In `Safepoint \"G1CollectForAllocation\" ... Reaching safepoint: 48000000 ns ... At safepoint: 2100000 ns`, where would you look first?",
   "options": [
    "At the GC settings, because the collection took 48 ms",
    "At application code that runs a long time without a safepoint check",
    "At the heap size, because the heap is too small",
    "At the number of GC worker threads"
   ],
   "answer": 1,
   "why": "\"Reaching safepoint\" is the time the slowest thread took to stop: 48 ms here. The GC work itself, \"At safepoint\", took 2.1 ms. A long time-to-safepoint means some thread ran far without reaching a safepoint check, which no GC setting fixes."
  },
  {
   "q": "From lesson 2: why is a dead 3 MiB array cheaper for G1 than a 3 MiB array that survives several young pauses, even though both are humongous?",
   "options": [
    "Dead humongous objects can be reclaimed in a young pause without any copying; live ones keep their contiguous regions and fill the old generation",
    "Live humongous objects are copied in every young pause",
    "Dead humongous objects go into a TLAB",
    "There is no difference; G1 treats all humongous objects alike"
   ],
   "answer": 0,
   "why": "Humongous objects never go through TLABs or eden, and G1 never copies them. The demo showed a young pause freeing `Humongous regions: 12->0` because the arrays were already dead. A live one keeps its regions as part of the old generation until it dies and a collection finds it.",
   "from": "mem-02"
  }
 ],
 "flashcards": [
  {"front": "What does the weak generational hypothesis say?", "back": "Most objects die young. Collectors use it by collecting a small young generation often and the old generation rarely."},
  {"front": "What does a young collection's pause time depend on?", "back": "Mostly on how much survives and must be copied, not on how much garbage there is."},
  {"front": "What does a write barrier do in a generational collector?", "back": "On every reference store, it marks the card (512 bytes in G1) that holds the field as dirty, so a young GC scans dirty cards instead of the whole old generation."},
  {"front": "How does G1 pick its region size by default?", "back": "Max heap / 2048, clamped to 1 to 32 MB, rounded up to a power of two."},
  {"front": "When is an object humongous in G1?", "back": "When it is bigger than half a region. It gets whole contiguous regions and skips TLABs and eden."},
  {"front": "Which old regions can a G1 mixed collection take?", "back": "Regions under 85% live (`G1MixedGCLiveThresholdPercent`), best first, until the remaining garbage is within 5% of the heap."},
  {"front": "Two objects point at each other and nothing else points at them. Does a tracing GC free them?", "back": "Yes. Marking only asks whether a root can reach an object, so an unreachable cycle is never marked and gets freed."}
 ],
 "terms": [
  {"term": "Young generation", "plain": "Eden plus survivor space, where new objects live until they die or are promoted."},
  {"term": "Promotion", "plain": "Moving an object that survived enough young collections into the old generation."},
  {"term": "Evacuation", "plain": "G1's word for copying live objects out of a region so the region can be freed."},
  {"term": "Safepoint", "plain": "A moment when every application thread is stopped at a known place, so the GC can move objects."},
  {"term": "Card table", "plain": "One byte per 512-byte card of heap, marked dirty when a reference in that card changes."},
  {"term": "Remembered set", "plain": "G1's per-region list of cards elsewhere in the heap that point into the region."},
  {"term": "Humongous object", "plain": "In G1, an object bigger than half a region, stored in its own contiguous regions."},
  {"term": "Mixed collection", "plain": "A G1 pause that evacuates the young regions plus some old regions with the most garbage."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate, in your own words, what happens between G1's `Pause Young (Concurrent Start)` and its first `Pause Young (Mixed)`, and why G1 needs that step at all.",
  "answer": "Young pauses only clean eden and survivor regions, so the old regions slowly fill with promoted objects. When old-generation occupancy crosses the IHOP threshold, the next young pause also starts a concurrent marking cycle. Marking runs on background threads while the application keeps going, and a write barrier records overwritten references so nothing live is missed. Two short pauses, Remark and Cleanup, finish it. Now G1 knows how much of each old region is live. After one more young-only pause (Prepare Mixed), the mixed pauses evacuate young regions plus the old regions with the most garbage, at least an eighth of the candidates each time. Without marking, G1 couldn't know which old regions are worth copying, and the old generation would only be cleaned by a full GC."
 },
 "deeper": {
  "minutes": 10,
  "body": "The `-Xlog:gc*` version of a young pause shows where the time goes. From a 1 GB heap on JDK 21:\n\n```text\nGC(3) Using 4 workers of 4 for evacuation\nGC(3)   Pre Evacuate Collection Set: 0.32ms\nGC(3)   Merge Heap Roots: 0.04ms\nGC(3)   Evacuate Collection Set: 15.51ms\nGC(3)   Post Evacuate Collection Set: 0.25ms\nGC(3)   Other: 0.08ms\nGC(3) Eden regions: 120->0(199)\nGC(3) Survivor regions: 13->14(17)\nGC(3) Old regions: 2->9\nGC(3) Humongous regions: 8->0\nGC(3) Pause Young (Normal) (G1 Evacuation Pause) 141M->20M(1024M) 16.335ms\n```\n\nAlmost all of the 16 ms is \"Evacuate Collection Set\", the copying. \"Merge Heap Roots\" is the remembered-set work from section 3, tiny here. `Eden regions: 120->0(199)` means 120 eden regions before, none after, and a target of 199 for the next cycle: G1 resizes eden after every pause to meet its pause goal. `Old regions: 2->9` means 7 regions' worth of objects were promoted.\n\nThe G1 defaults behind this lesson, from the JDK 25 source: `InitiatingHeapOccupancyPercent` 45 with `G1UseAdaptiveIHOP` on, `G1MixedGCCountTarget` 8, `G1HeapWastePercent` 5, `G1MixedGCLiveThresholdPercent` 85 (an experimental flag), `G1ReservePercent` 10 (free space G1 tries to keep for copying), and `MaxTenuringThreshold` 15. `MaxGCPauseMillis` defaults to 200 once G1 is selected.\n\nOne more line you may meet: `Concurrent Undo Cycle`. It appears when a humongous allocation requested a concurrent start, but by the time marking would begin, occupancy was back under the threshold, so G1 abandoned the cycle. That reading comes from the logs, not from G1's documentation."
 },
 "sources": [
  {"title": "g1CollectedHeap.hpp at jdk-25-ga: humongous threshold", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1CollectedHeap.hpp"},
  {"title": "g1Policy.cpp at jdk-25-ga: mixed collection limits", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1Policy.cpp"},
  {"title": "g1BarrierSet.hpp at jdk-25-ga: the SATB logging barrier", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1BarrierSet.hpp"},
  {"title": "g1_globals.hpp at jdk-25-ga: G1 flags and defaults", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1_globals.hpp"}
 ]
}

def move_answer(q, to):
    """Put the correct option at index `to`, keeping the others in order."""
    right = q["options"].pop(q["answer"])
    q["options"].insert(to, right)
    q["answer"] = to


for q, to in zip(L["quiz"], [2, 1, 3, 1, 0]):
    move_answer(q, to)

(ROOT / "content/lessons/mem-04.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-04")
