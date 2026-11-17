import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/memory/src"
P = "java/workbench/memory/l07"
K = "kotlin/workbench/memory/l07"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :memory:demo -Pmain=workbench.memory.l07."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIGURE = """<svg viewBox="0 0 680 300" role="img" aria-label="The leaking thumbnail cache as a chain: a static field holds a ConcurrentHashMap, its table, 20,000 nodes, 20,000 thumbnails and keys, and 20,000 pixel arrays of 2 KB. Everything below the map is its retained set, about 44 MB. A shared format string that another root, the list of formats, also reaches is not part of it">
<rect class="box-dim" x="24" y="56" width="282" height="232" rx="8"/>
<rect class="box-a" x="40" y="16" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="37" text-anchor="middle">GC root: static THUMBNAILS</text>
<rect class="box" x="40" y="62" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="83" text-anchor="middle">ConcurrentHashMap: 64 B</text>
<rect class="box" x="40" y="108" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="129" text-anchor="middle">Node[] table: 128 KB</text>
<rect class="box" x="40" y="154" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="175" text-anchor="middle">20,000 nodes: 32 B each</text>
<rect class="box" x="40" y="200" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="221" text-anchor="middle">20,000 thumbnails and keys</text>
<rect class="box-bad" x="40" y="246" width="250" height="34" rx="8"/>
<text class="t-s" x="165" y="267" text-anchor="middle">20,000 pixel arrays: 2,064 B each</text>
<line class="ln" x1="165" y1="50" x2="165" y2="60" marker-end="url(#arr)"/>
<line class="ln" x1="165" y1="96" x2="165" y2="106" marker-end="url(#arr)"/>
<line class="ln" x1="165" y1="142" x2="165" y2="152" marker-end="url(#arr)"/>
<line class="ln" x1="165" y1="188" x2="165" y2="198" marker-end="url(#arr)"/>
<line class="ln" x1="165" y1="234" x2="165" y2="244" marker-end="url(#arr)"/>
<text class="t-s" x="425" y="100" text-anchor="middle">retained by the map: about 44 MB</text>
<text class="t-s t-m" x="425" y="122" text-anchor="middle">tear up the noticeboard's list</text>
<text class="t-s t-m" x="425" y="140" text-anchor="middle">and all of it becomes garbage</text>
<rect class="box-a" x="440" y="16" width="220" height="34" rx="8"/>
<text class="t-s" x="550" y="37" text-anchor="middle">GC root: static FORMATS</text>
<rect class="box-b" x="440" y="200" width="220" height="34" rx="8"/>
<text class="t-s" x="550" y="221" text-anchor="middle">shared "image/jpeg" string</text>
<line class="ln" x1="550" y1="50" x2="550" y2="198" marker-end="url(#arr)"/>
<line class="ln-d" x1="290" y1="217" x2="438" y2="217" marker-end="url(#arr)"/>
<text class="t-s t-m" x="550" y="258" text-anchor="middle">another root reaches it too,</text>
<text class="t-s t-m" x="550" y="276" text-anchor="middle">so the map does not retain it</text>
</svg>"""

OPENING = """Back in the warehouse, the floor keeps filling, and the cleaning crew isn't to blame. It throws out every box that no note leads to, exactly as it should. The trouble is a list pinned to the noticeboard by the door, which someone started months ago and never stopped writing. Every shelf number on that list is a box the crew must keep. Nobody needs those boxes. Somebody still holds a note to them.

That's a memory leak in Java, and it surprises anyone who learned the word in C, a language with no garbage collector, where a leak is memory nobody can reach any more. The last lesson showed the symptoms: a floor that rises in the GC log, or a container that grows until the kernel ends it. The easy trap is to reach for a heap dump every time. A heap dump photographs the floor, and it can't see the yard out back.

In this lesson, we'll make the thumbnail service leak, count what piles up, photograph the floor to find the list, then measure the yard and give memory out there a return date. Before we start, make a guess, and keep it in mind."""

S1 = """The garbage collector, the JVM's cleaning crew, frees every object on the heap (the memory where objects live) that it can't reach from a GC root. (A GC root is a starting point it trusts: a local variable on a thread's stack, one of the workers' desks, or a static field, the noticeboard by the door.) So in Java, a **leak** is memory that stays reachable from a root after the program is done with it. The collector is doing its job. Your code still holds the reference.

Here's the classic one, a thumbnail cache with no limit. It's a static map from an upload id to its thumbnail, so the service can send the same picture again without redoing the work:

```java
static final Map<String, CachedThumbnail> THUMBNAILS = new ConcurrentHashMap<>();   // never evicted

static void handle(String uploadId) {
    THUMBNAILS.computeIfAbsent(uploadId,
            id -> new CachedThumbnail(id, System.currentTimeMillis(), FORMATS.get(0), new byte[2_048]));
}
```

```kotlin
private val THUMBNAILS = ConcurrentHashMap<String, KCachedThumbnail>()          // never evicted

private fun handle(uploadId: String) {
    THUMBNAILS.computeIfAbsent(uploadId) { id ->
        KCachedThumbnail(id, System.currentTimeMillis(), FORMATS[0], ByteArray(2_048))
    }
}
```

`FORMATS` is a static list of the picture formats the site accepts, and each thumbnail points at one of its strings; that will matter in the next section. Every upload adds an entry, and nothing ever removes one. Lesson 6 showed what that looks like in a GC log: the after-values of young pauses rise pass after pass, full GCs (collections of the whole heap) free less and less, and in the end the JVM throws `OutOfMemoryError` or spends its time in `Pause Full`.

The same shape turns up in four places, over and over:

- maps and caches with no limit and no expiry;
- `ThreadLocal` values, a separate value per thread, set on the threads of a thread pool and never removed, so each pool thread keeps its last value forever (the threads track showed one);
- listeners, objects registered to be called back when something happens, that nobody unregisters (lesson 3's weak registry is one fix);
- class loaders, the parts of the JVM that load a program's classes, that can't be unloaded, which shows up as growth in metaspace, the back room where class plans live, and as collections with the cause `Metadata GC Threshold`.

The first tool is a **class histogram**: a count of live objects, and their bytes, for every class. `jcmd <pid> GC.class_histogram` prints one after a full GC, so it counts only reachable objects. (`jcmd` is the JDK's tool for sending commands to a running JVM, and `<pid>` is its process id.) For the cache above, after 20,000 uploads on JDK 25, the top four rows were:

```text
 num     #instances         #bytes  class name (module)
   1:         52891       43157184  [B (java.base@25.0.5.0.3)
   2:         32777         786648  java.lang.String (java.base@25.0.5.0.3)
   3:         22654         724928  java.util.concurrent.ConcurrentHashMap$Node (java.base@25.0.5.0.3)
   4:         20000         640000  workbench.memory.l07.LeakDemo$CachedThumbnail
```

`[B` means `byte[]`. Exactly 20,000 thumbnails of 32 bytes each are alive, 20,000 more than anyone meant to keep. That's the clue. The histogram tells you what fills the floor. It can't tell you who holds it."""

S2 = """A **heap dump** is a file with every object on the heap and every reference between them, in a format called HPROF. It's a photograph of every shelf, taken for a detective. You can take one three ways:

- `jcmd <pid> GC.heap_dump /tmp/app.hprof` from a running JVM. Its help text says "Impact: High": it runs a full GC first (unless you pass `-all`) and stops the JVM while it writes. `-gz` compresses the file, and on JDK 25 `-parallel` sets how many threads write it.
- `-XX:+HeapDumpOnOutOfMemoryError` with `-XX:HeapDumpPath=...`, so the JVM writes one the moment it runs out of heap. It's off by default. It's a manageable flag, so `jcmd <pid> VM.set_flag HeapDumpOnOutOfMemoryError true` turns it on in a running JVM.
- `HotSpotDiagnosticMXBean.dumpHeap(path, true)` from code, which is what the demo does.

You read the photograph with a tool such as Eclipse MAT (Memory Analyzer), a free program from the Eclipse project. It shows two sizes for every object. The **shallow size** is the object's own bytes: lesson 1's header plus fields. The **retained size** is everything that would be freed if that one object were gone: the object itself plus everything reachable only through it.

You can work out a retained size by hand on a small graph, and doing it once makes MAT's numbers obvious. Look at the figure. The noticeboard's static field holds the map. The map holds a table, the table holds 20,000 nodes, and each node holds a key and a thumbnail with its 2 KB of pixels. Every path from a root to those pixels goes through the map, so the map **dominates** them, and they're in its retained set. Add it up: 20,000 pixel arrays at 2,064 bytes, keys at 80, thumbnails at 32 and nodes at 32, plus the 128 KB table. That's about 44 MB, held by a 64-byte object.

The shared `"image/jpeg"` string is different. The `FORMATS` list, another static field, reaches it too, so dropping the map wouldn't free it. It isn't in the map's retained set.

Is the arithmetic right? Let's not take my word for it. The demo measures the live heap after a full GC, clears the map, and measures again. On JDK 25 it printed:

```text
live heap 47,259,896 bytes with the cache full, 2,763,024 after clear(): it kept 44,496,872 bytes alive
```

That's 44.5 MB, the retained set we added up, give or take a little noise. (`clear()` keeps the map's table, which the hand count included.)

MAT's **dominator tree** lists objects by retained size, biggest first. For this dump, the map should sit at the top with about 44 MB, and its path to a GC root should name the static field `THUMBNAILS`. (I couldn't run MAT for this course, so that's what the definition and the measurement predict, not a screenshot.) **A histogram says what fills the floor. The dominator tree says who holds it. Fix the holder.**

Here the photograph picture breaks. A photo shows one moment, while a leak is a habit: the code adds a note on every upload. You find the list in the dump, but you fix it in the code that keeps writing it.

And a photograph of the floor can't show what isn't on the floor."""

S3 = """Sometimes the heap is fine and the process still grows. The GC log shows a flat floor, a heap dump shows nothing odd, and the container still gets killed. The memory is outside the heap, in the yard out back that the floor plan doesn't show.

**Native Memory Tracking** (NMT) is the JVM's own inventory of the memory it uses, the yard included. It's off by default. Start the JVM with `-XX:NativeMemoryTracking=summary`, then ask the running process:

```text
jcmd <pid> VM.native_memory summary scale=MB
```

In the demo, a JDK 25 process with a 256 MB heap had committed 295 MB at startup (committed means the operating system has really handed it over). Then it allocated one 64 MiB direct buffer, memory outside the heap that `ByteBuffer.allocateDirect` asks for, and started 100 threads. Now it had committed 370 MB. NMT shows where the difference went. A category called `Other` appeared with 64 MB, the direct buffer. `Thread` went from 1 MB to 11 MB committed, with 120 MB reserved (addresses set aside, not yet used), because each new thread reserves about 1 MB for its stack but touches only a little of it.

For a slow leak, take a baseline and compare later:

```text
jcmd <pid> VM.native_memory baseline
jcmd <pid> VM.native_memory summary.diff scale=MB
```

The diff marks every change. After 100 direct buffers of 1 MiB, JDK 25 printed:

```text
-                     Other (reserved=100MB +100MB, committed=100MB +100MB)
                            (malloc=100MB +100MB #102 +100)
```

A growing `Other` points at direct buffers or native code, a growing `Thread` at threads that are started and never stopped, and a growing `Class` or `Metaspace` at class loaders.

Direct buffers deserve one more level of detail. `ByteBuffer.allocateDirect` creates a small object on the heap that owns the native memory. When the GC collects that small object, a cleaner frees the memory, the same idea as lesson 3's `Cleaner`. In the warehouse, each crate in the yard has a tag on the floor, and the crate goes only when the crew throws out its tag. So native memory waits for a collection, and a big, quiet heap may not collect for a long time.

Unless you set `-XX:MaxDirectMemorySize`, the limit for all of it is the max heap size. Set it, and a direct-buffer leak fails loudly instead of quietly, with a stack trace that points at the code:

```text
java.lang.OutOfMemoryError: Cannot reserve 67108864 bytes of direct buffer memory (allocated: 0, limit: 33554432)
```

A crate that leaves only when the crew passes by is awkward, though. Sometimes you know exactly when you're done with it."""

S4 = """The Foreign Function and Memory API (FFM), final since JDK 22 (JEP 454), gives memory outside the heap a lifetime you control. Memory comes from an **arena**, and the arena decides when that memory is freed. In the warehouse, an arena is a corner of the yard rented with a return date, handed back all at once.

| Arena | Lifetime | Closed by | Threads |
|---|---|---|---|
| `Arena.global()` | until the JVM exits | nobody | any |
| `Arena.ofAuto()` | until the GC finds it unreachable | the GC | any |
| `Arena.ofConfined()` | until you call `close()` | you, from the owner thread | the owner only |
| `Arena.ofShared()` | until you call `close()` | you, from any thread | any |

A confined arena in try-with-resources frees its memory at the closing brace. No GC is involved, so there's nothing to wait for. A **memory segment** is the block of memory an arena hands out:

```java
try (Arena arena = Arena.ofConfined()) {
    MemorySegment block = arena.allocate(32L * 1024 * 1024);   // 32 MiB outside the heap
    block.setAtIndex(ValueLayout.JAVA_LONG, 0, 1_999);
}                                                              // freed here
```

```kotlin
Arena.ofConfined().use { arena ->
    val block = arena.allocate(32L * 1024 * 1024)              // 32 MiB outside the heap
    block.setAtIndex(ValueLayout.JAVA_LONG, 0, 1_999)
}                                                              // freed here
```

If code uses a segment after its arena is closed, it gets an `IllegalStateException` with the message `Already closed`. In C, the same mistake reads freed memory and may silently corrupt data.

The accounting holds a surprise on JDK 25. NMT counts the confined arena's memory under `Other`: `Other (reserved=32MB, committed=32MB)` inside the arena, and `0MB` after `close()`. But the JDK's direct buffer pool, and with it `-XX:MaxDirectMemorySize`, counts only automatic arenas. In JDK 25's source, one line decides it: an arena counts its memory as direct memory only when the GC manages the arena's lifetime. That makes sense once you see it. An automatic arena waits for the GC, like a direct buffer, so it shares their limit; a confined arena is freed when you say so. With `-XX:MaxDirectMemorySize=16m`, the demo's confined 32 MiB worked, and its automatic 32 MiB failed with `Cannot reserve 33554432 bytes of direct buffer memory`.

The labs compile for JDK 21, where FFM is still a preview, so this demo is a single file that runs outside Gradle on JDK 22 or later.

That's also where today's tools stop. A heap dump is one moment of the floor, NMT counts categories rather than callers, and neither one names the line of code that keeps writing the list. They tell you where to look. Reading that code is still your job."""

L = {
 "id": "mem-07",
 "title": "Hunting memory leaks: heap dumps, native memory and off-heap",
 "minutes": 38,
 "goal": "By the end you can tell a heap leak from growth outside the heap, find who holds a leaked object with a histogram, a heap dump and its dominator tree, measure native memory with NMT, give off-heap memory a lifetime with an arena, and fix a leaking cache.",
 "opening": OPENING,
 "warmup": {
  "q": "A service's GC log shows young pauses ending at a flat 300 MB for days, yet its container keeps growing until the kernel kills it. Where should you look first?",
  "options": ["A heap dump: the leak must be in the heap", "Memory outside the heap: direct buffers, threads, metaspace, with Native Memory Tracking", "The young generation size", "The GC pause goal"],
  "answer": 1,
  "why": "A flat floor after young pauses means the live heap isn't growing, so a heap dump will look normal. The growth is outside the heap, where Native Memory Tracking, the direct buffer pool and the thread count can show it. The young generation size and the pause goal change how the heap is collected, not what grows beside it."
 },
 "sections": [
  {
   "h": "A box nobody needs, still on a note: what a Java leak is",
   "body": S1,
   "try": {
    "title": "Leak, count, dump",
    "minutes": 4,
    "steps": [
     "Read `LeakDemo`. Its first child JVM handles 20,000 uploads with the cache above, prints the top of the class histogram, writes a heap dump, and measures what the cache keeps alive. Its second child has `-Xmx64m -XX:+HeapDumpOnOutOfMemoryError` and handles uploads until the heap is full.",
     "Predict: which class tops the histogram, and how many `CachedThumbnail` objects are alive?",
     "Run it."
    ],
    "code": demo("LeakDemo"),
    "expect": "`[B` (byte arrays) tops the list with about 43 MB, then `String`, `ConcurrentHashMap$Node`, and exactly 20,000 `CachedThumbnail` objects (`KCachedThumbnail` in the Kotlin twin) at 32 bytes each. A fifth row, `jdk.internal.vm.FillerElement`, is the JVM's filler for unused gaps in the heap; skip it. The dump `leak.hprof` is about 52 MB, in `labs/memory/build/heapdumps/`, and the last line says the cache kept about 44.5 MB alive. The second child prints `java.lang.OutOfMemoryError: Java heap space`, `Dumping heap to build/heapdumps/oom.hprof ...` and `Heap dump file created [...]` (about 72 MB), plus a line about the error being thrown again from the handler for uncaught exceptions."
   },
   "refs": [
    {"title": "The jcmd command, JDK 25 man page source: GC.class_histogram and GC.heap_dump", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md", "kind": "docs"}
   ]
  },
  {
   "h": "A photo of every shelf: heap dumps, retained size and the dominator tree",
   "body": S2,
   "figure": {"svg": FIGURE, "caption": "Everything below the map is reachable only through it, so it is the map's retained set. The shared format string has another root, so the map doesn't retain it."},
   "try": {
    "title": "Find the holder in Eclipse MAT",
    "minutes": 6,
    "steps": [
     "Download Eclipse Memory Analyzer (MAT) from the Eclipse website, and open `labs/memory/build/heapdumps/leak.hprof` from the previous demo.",
     "Before you click anything, predict the top entry of the dominator tree and its retained size, from the figure and the demo's last line.",
     "Open the dominator tree. Then, on the biggest entry, use \"Path to GC Roots\" to find the field that holds it."
    ],
    "expect": "From the definition and the measurement, the `ConcurrentHashMap` should top the dominator tree with a retained size of about 44 MB, almost all of it in 2 KB `byte[]` pixel arrays. Its path to a GC root should end at the static field `THUMBNAILS` of `LeakDemo`. If your top entry is something else, compare its retained size with the histogram's byte counts and follow its path to the root the same way."
   },
   "refs": [
    {"title": "Eclipse MAT help: dominator tree", "url": "https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/dominatortree.html", "kind": "docs"},
    {"title": "Eclipse MAT help: shallow and retained heap", "url": "https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/shallowretainedheap.html", "kind": "docs"}
   ]
  },
  {
   "h": "The yard out back: Native Memory Tracking finds growth outside the heap",
   "body": S3,
   "try": {
    "title": "Watch native memory move",
    "minutes": 4,
    "steps": [
     "Read `NmtDemo`. Its first child runs with `-XX:NativeMemoryTracking=summary` and prints NMT's summary before and after a 64 MiB direct buffer and 100 threads. Its second child asks for 64 MiB of direct memory under `-XX:MaxDirectMemorySize=32m`.",
     "Predict which NMT categories change, and by how much. Then run it."
    ],
    "code": demo("NmtDemo"),
    "expect": "`Java Heap` stays at 216 MB committed. `Other` appears with 64 MB, the direct buffer. `Thread` grows from about 1 MB to 11 MB committed and from 18 MB to about 120 MB reserved: 100 stacks of about 1 MB each, mostly untouched. `Total` committed rises by about 75 MB, from 295 to 370 MB on JDK 25. The second child prints `Cannot reserve 67108864 bytes of direct buffer memory (allocated: 0, limit: 33554432)`."
   }
  },
  {
   "h": "Off-heap memory with a return date: arenas in the FFM API",
   "body": S4,
   "try": {
    "title": "Free 32 MiB at a closing brace (JDK 22 or later)",
    "minutes": 4,
    "steps": [
     "This one runs outside Gradle and needs JDK 22 or later, ideally 25. Check with `java -version`. From `labs/`, run `java -XX:NativeMemoryTracking=summary memory/jdk25/ArenaDemo.java`. The Kotlin twin needs `kotlinc`; its commands are at the top of `ArenaDemo.kt`.",
     "Predict the `Other` line inside the arena and after `close()`, then run it.",
     "Run it again with `-XX:MaxDirectMemorySize=16m` in place of the NMT flag, and see which of the two arenas the limit stops."
    ],
    "code": {"lang": "java", "title": "ArenaDemo.java (JDK 22 or later)", "src": read("labs/memory/jdk25/ArenaDemo.java"),
             "run": "java -XX:NativeMemoryTracking=summary memory/jdk25/ArenaDemo.java", "file": "labs/memory/jdk25/ArenaDemo.java",
             "alt": {"lang": "kotlin", "title": "ArenaDemo.kt (JDK 22 or later)", "src": read("labs/memory/jdk25/ArenaDemo.kt"),
                     "run": "kotlinc memory/jdk25/ArenaDemo.kt -include-runtime -d memory/build/arena-demo.jar && java -XX:NativeMemoryTracking=summary -jar memory/build/arena-demo.jar",
                     "file": "labs/memory/jdk25/ArenaDemo.kt"}},
    "expect": "On JDK 25: `entry 1,000 holds 100000`, then `Other (reserved=32MB, committed=32MB)` inside the arena and `Other (reserved=0MB, committed=0MB)` after `close()`, then `reading after close() throws: Already closed` and `an automatic arena: 32 MiB counted as direct memory`. With `-XX:MaxDirectMemorySize=16m` the confined arena still works (the NMT lines just ask for the NMT flag), and the automatic arena fails with `OutOfMemoryError: Cannot reserve 33554432 bytes of direct buffer memory (allocated: 0, limit: 16777216)`."
   },
   "refs": [
    {"title": "JEP 454: Foreign Function & Memory API", "url": "https://openjdk.org/jeps/454", "kind": "read"},
    {"title": "ArenaImpl.java at jdk-25-ga: which arenas reserve direct memory", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/foreign/ArenaImpl.java", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A bounded LRU cache in Java and Kotlin",
  "java": {"title": "LruCache.java", "src": "final class LruCache<K, V> {\n    private final Map<K, V> map;\n\n    LruCache(int maxEntries) {\n        // true = access order: get() moves an entry to the end, so the eldest is the least recently used\n        map = new LinkedHashMap<>(16, 0.75f, true) {\n            @Override\n            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {\n                return size() > maxEntries;\n            }\n        };\n    }\n\n    synchronized V get(K key) { return map.get(key); }\n    synchronized void put(K key, V value) { map.put(key, value); }\n}"},
  "kotlin": {"title": "LruCache.kt", "src": "class LruCache<K, V>(private val maxEntries: Int) {\n    // true = access order: get() moves an entry to the end, so the eldest is the least recently used\n    private val map = object : LinkedHashMap<K, V>(16, 0.75f, true) {\n        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<K, V>?): Boolean =\n            size > maxEntries\n    }\n\n    @Synchronized fun get(key: K): V? = map[key]\n    @Synchronized fun put(key: K, value: V) { map[key] = value }\n}"},
  "note": "LRU means least recently used: when the cache is full, the entry nobody has asked for the longest goes first. Both versions build on the same JDK class, and both need the lock, because `LinkedHashMap` isn't thread-safe and in access order even `get` changes the map. Java overrides `removeEldestEntry` in an anonymous subclass; Kotlin does it with an `object :` expression, and its `eldest` parameter is nullable because the JDK doesn't say whether it can be null. Kotlin returns `V?` from `get`, which puts the cache miss in the type. In a real service you'd often use a cache library with size limits and expiry, but the leak fix is the same idea in every form: decide a maximum, and make the structure enforce it."
 },
 "worked": {
  "title": "From a killed container to the line that leaks",
  "steps": [
   {"say": "Picture an album exporter, a background job of the photo site that packs a user's photos into one download. Suppose it restarts with exit code 137 every two days. Start with the GC log, because it decides which half of memory to look at. Say its young pauses end near the same value day after day: the live heap is flat, so a heap dump would look healthy. Don't start there.",
    "code": "", "lang": ""},
   {"say": "1. Measure the yard. Restart one instance with NMT, take a baseline once it's warm, and diff it a few hours later. Suppose only one category moved: `Other`, by hundreds of megabytes, with thousands more native allocations.",
    "code": "java -XX:NativeMemoryTracking=summary ... -jar album-exporter.jar\njcmd <pid> VM.native_memory baseline\n# a few hours later\njcmd <pid> VM.native_memory summary.diff scale=MB",
    "lang": "text"},
   {"say": "2. Name the suspect. A growing `Other` is direct buffers or native code, and the JDK's direct buffer pool confirms it if its count and size keep climbing. Then find who allocates direct buffers for each album. Here it's a map that keeps one buffer per album and never removes them.",
    "code": "// 1. the leak: one direct buffer per album, kept forever\nprivate final Map<String, ByteBuffer> albumBuffers = new ConcurrentHashMap<>();\n\nByteBuffer bufferFor(String albumId) {\n    return albumBuffers.computeIfAbsent(albumId, id -> ByteBuffer.allocateDirect(1 << 20));\n}",
    "lang": "java",
    "alt_code": "// 1. the leak: one direct buffer per album, kept forever\nprivate val albumBuffers = ConcurrentHashMap<String, ByteBuffer>()\n\nfun bufferFor(albumId: String): ByteBuffer =\n    albumBuffers.computeIfAbsent(albumId) { ByteBuffer.allocateDirect(1 shl 20) }",
    "alt_lang": "kotlin"},
   {"say": "3. Fix the lifetime, then add a guard. Give each album its memory for exactly as long as it's being packed, with a confined arena (JDK 22 or later), or remove the buffer from the map when the album is done. Then cap direct memory, so the next direct-buffer leak fails as an `OutOfMemoryError` with a stack trace instead of a silent kill. The cap doesn't cover confined arenas; you close those yourself.",
    "code": "void packAlbum(String albumId, Album album) {\n    try (Arena arena = Arena.ofConfined()) {             // 2. memory lives exactly as long as the album is packed\n        MemorySegment buffer = arena.allocate(1 << 20);\n        album.writeInto(buffer);\n        upload(albumId, buffer);\n    }                                                    // 3. freed here, no GC needed\n}\n// and on the command line: -XX:MaxDirectMemorySize=128m",
    "lang": "java",
    "alt_code": "fun packAlbum(albumId: String, album: Album) {\n    Arena.ofConfined().use { arena ->                    // 2. memory lives exactly as long as the album is packed\n        val buffer = arena.allocate(1 shl 20)\n        album.writeInto(buffer)\n        upload(albumId, buffer)\n    }                                                    // 3. freed here, no GC needed\n}\n// and on the command line: -XX:MaxDirectMemorySize=128m",
    "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Find and fix the leaks in an upload cache",
  "minutes": 14,
  "files": [
   "labs/memory/src/main/java/workbench/memory/l07/UploadCache.java",
   "labs/memory/src/main/java/workbench/memory/l07/PhotoUpload.java",
   "labs/memory/src/main/java/workbench/memory/l07/UploadResult.java"
  ],
  "run": "./gradlew :memory:test --tests 'workbench.memory.l07.*'",
  "steps": [
   "Read `UploadCache`. A phone on a weak connection often sends the same upload twice, because it never heard the first answer, so the cache remembers the result for each upload id and hands it back on a retry. It also rejects a retry whose photo differs from the original.",
   "Run the tests. Four of six fail. The two that pass check behaviour: a retry gets the same result, and a reused upload id with a different photo is rejected. Keep those passing.",
   "Read the failing messages. Two tests count live objects with the class histogram, the same one `jcmd GC.class_histogram` prints: after 20,000 uploads, 20,000 results and 20,000 uploads are still alive.",
   "Fix the first leak: bound the cache to `maxEntries` with an access-ordered `LinkedHashMap` and `removeEldestEntry`, and make the methods `synchronized`.",
   "Run the tests again. The upload test still fails, now with about 500. Find out why each entry keeps its whole `PhotoUpload`, and replace it with what the retry check really needs: a SHA-256 digest of the photo. Run the tests until all six pass."
  ],
  "hints": [
   "`new LinkedHashMap<>(16, 0.75f, true)` makes the map access-ordered. Override `removeEldestEntry` to return `size() > maxEntries`.",
   "`MessageDigest.getInstance(\"SHA-256\").digest(photo)` gives 32 bytes, a fingerprint of the photo. Compare two digests with `MessageDigest.isEqual`.",
   "The entry record is private, so you can change its fields freely, for example to `record Entry(byte[] photoDigest, UploadResult result)`.",
   "The leak tests allow 2 stray objects, because the test's own last local variables may still be reachable while it counts."
  ],
  "done_when": "All 6 tests in `UploadCacheTest` pass."
 },
 "drill": {
  "title": "Write the first commands from memory",
  "minutes": 4,
  "prompt": "Close the page. A program's container keeps growing. Write the commands you'd run, in order, to decide whether it's a heap leak or growth outside the heap, and to collect evidence for each case. Then write a bounded LRU map from memory.",
  "answer": {
   "lang": "java",
   "src": "// 1. which half? read the floor of the young pauses in the GC log (rising = heap, flat = outside it)\n// 2. heap:    jcmd <pid> GC.class_histogram          (what)\n//             jcmd <pid> GC.heap_dump /tmp/app.hprof  (who: dominator tree in MAT)\n// 3. outside: start with -XX:NativeMemoryTracking=summary, then\n//             jcmd <pid> VM.native_memory baseline\n//             jcmd <pid> VM.native_memory summary.diff scale=MB\nstatic <K, V> Map<K, V> lru(int maxEntries) {\n    return Collections.synchronizedMap(new LinkedHashMap<K, V>(16, 0.75f, true) {\n        @Override protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {\n            return size() > maxEntries;\n        }\n    });\n}",
   "alt": {
    "lang": "kotlin",
    "src": "// 1. which half? read the floor of the young pauses in the GC log (rising = heap, flat = outside it)\n// 2. heap:    jcmd <pid> GC.class_histogram          (what)\n//             jcmd <pid> GC.heap_dump /tmp/app.hprof  (who: dominator tree in MAT)\n// 3. outside: start with -XX:NativeMemoryTracking=summary, then\n//             jcmd <pid> VM.native_memory baseline\n//             jcmd <pid> VM.native_memory summary.diff scale=MB\nfun <K, V> lru(maxEntries: Int): MutableMap<K, V> =\n    Collections.synchronizedMap(object : LinkedHashMap<K, V>(16, 0.75f, true) {\n        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<K, V>?) = size > maxEntries\n    })"
   }
  }
 },
 "recap": [
  "A Java leak is memory that stays reachable from a GC root after you're done with it: caches with no limit, ThreadLocals on pool threads, forgotten listeners, class loaders that can't unload.",
  "A rising floor in the GC log means a heap leak. `jcmd GC.class_histogram` says what fills the heap; a heap dump and MAT's dominator tree say who holds it, ranked by retained size, with the path to the field.",
  "A flat floor with a growing process means memory outside the heap. Start with `-XX:NativeMemoryTracking=summary`, take a `baseline`, and read `summary.diff`.",
  "Direct buffers are freed only after a GC collects their small heap objects, and their default limit is the max heap. Set `-XX:MaxDirectMemorySize` so a leak fails loudly.",
  "FFM arenas (final in JDK 22) give off-heap memory a lifetime: a confined arena frees it at `close()`. On JDK 25 only automatic arenas count against the direct-memory limit; NMT shows all of them under `Other`.",
  "The limit of today's tools: a heap dump is one moment and NMT counts categories, not callers. They tell you where to look, but finding the code that keeps adding notes is still reading code."
 ],
 "closing": """We started with a list on the noticeboard that nobody stopped writing. A histogram counted its boxes, a heap dump and its dominator tree found the list, NMT took stock of the yard, and an arena handed yard space back at a closing brace. That ends this track, from the first box on the floor to the last crate out back.

Now search your own code for a static map or a cache with no maximum size, and for `ByteBuffer.allocateDirect`. For each one, ask what removes the entry, and when.

Next, we'll leave memory for time. A program gets faster while it runs, without a line changing. What does the JVM do to your code after it starts?""",
 "quiz": [
  {
   "q": "A class histogram after a full GC shows 2.1 million `byte[]` instances using 4.3 GB. What does that tell you about the leak?",
   "options": [
    "That `byte[]` is the leaking class, and the fix is to allocate fewer arrays",
    "What fills the heap, but not who holds it: you need the dominator tree of a heap dump",
    "That the leak is outside the heap",
    "Nothing, because the histogram counts garbage too"
   ],
   "answer": 1,
   "why": "Byte arrays sit under strings, buffers, pixels and file contents alike, so the histogram can't name the owner. `GC.class_histogram` runs a full GC first and counts only live objects. The dominator tree ranks objects by what they keep alive, and the path to a GC root names the field."
  },
  {
   "q": "In a heap dump, a `GalleryIndex` object has a shallow size of 24 bytes and a retained size of 1.2 GB. What does that mean?",
   "options": [
    "The index object itself is 1.2 GB",
    "If the index became unreachable, about 1.2 GB would be freed with it",
    "The index is referenced 1.2 billion times",
    "The dump is corrupt: retained size can't exceed shallow size by that much"
   ],
   "answer": 1,
   "why": "Shallow size is the object's own header and fields. Retained size adds everything reachable only through it, its retained set. A small object at the top of a big map routinely retains gigabytes, which makes it exactly the object to look at. The demo's 64-byte map kept 44 MB alive."
  },
  {
   "q": "A program's young pauses end at a flat 400 MB, but NMT's `summary.diff` after six hours shows `Thread (reserved=2150MB +1900MB, committed=210MB +185MB)`. What is leaking?",
   "options": ["Heap objects", "Threads: code keeps starting threads, each with its own stack, and never ends them", "Metaspace", "Direct buffers"],
   "answer": 1,
   "why": "About 1,900 MB more reserved stack is roughly 1,900 new threads at about 1 MB each, with a little of each stack touched. Look for a thread pool created for each request and never shut down, or a thread started per connection. Direct buffers would show in `Other`, and metaspace in `Class` and `Metaspace`."
  },
  {
   "q": "A program needs a 1 MiB off-heap buffer for each album it packs. Which choice frees each buffer as soon as its album is done, without waiting for a GC?",
   "options": [
    "`ByteBuffer.allocateDirect`, then drop the reference",
    "A segment from `Arena.ofConfined()` in try-with-resources",
    "A segment from `Arena.ofAuto()`",
    "A segment from `Arena.global()`"
   ],
   "answer": 1,
   "why": "A confined arena frees its memory when `close()` runs, at the end of the try block. A dropped direct buffer and an automatic arena are freed only after the GC finds them unreachable, which on a quiet heap can take a long time. The global arena is never freed."
  },
  {
   "q": "From the threads track: the tasks of a thread pool call `CURRENT_USER.set(upload.userId())` on a `ThreadLocal` and never call `remove()`. Which leak pattern is this, and what does a heap dump show as the GC root?",
   "options": [
    "A cache with no limit; the root is a static map",
    "A value kept alive by a long-lived pool thread; the root is the live thread itself",
    "A class loader leak; the root is the class loader",
    "Not a leak, because ThreadLocal values are weak"
   ],
   "answer": 1,
   "why": "Each thread keeps its own ThreadLocal values, and a pool thread lives as long as the pool. A started, unfinished thread is a GC root, so the last value each thread saw stays reachable. The `ThreadLocal` key is weak inside the thread's map, but the value is strong. The fix is `remove()` in a `finally` block.",
   "from": "conc-11"
  }
 ],
 "flashcards": [
  {"front": "What is a memory leak in Java?", "back": "Memory that stays reachable from a GC root after the program is done with it, so the GC may not free it."},
  {"front": "What does `jcmd <pid> GC.class_histogram` show, and what does it miss?", "back": "Live objects per class, after a full GC: what fills the heap. It doesn't show who holds them."},
  {"front": "Shallow size vs retained size?", "back": "Shallow: the object's own bytes. Retained: everything freed if that object went away, the object plus all it alone keeps reachable."},
  {"front": "How do you get a heap dump at the moment of an `OutOfMemoryError`?", "back": "`-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=...`. It's manageable, so `jcmd <pid> VM.set_flag HeapDumpOnOutOfMemoryError true` works on a running JVM."},
  {"front": "How do you find slow growth outside the heap?", "back": "Start with `-XX:NativeMemoryTracking=summary`, run `jcmd <pid> VM.native_memory baseline`, then later `jcmd <pid> VM.native_memory summary.diff`."},
  {"front": "When is a direct ByteBuffer's native memory freed?", "back": "After the GC collects the small buffer object on the heap and its cleaner runs. On a quiet heap that can take a long time."},
  {"front": "On JDK 25, which FFM arenas count against `-XX:MaxDirectMemorySize`?", "back": "Only automatic ones (`Arena.ofAuto()`), which wait for the GC like direct buffers. Confined and shared arenas are freed at `close()` and don't count; NMT shows them under `Other`."}
 ],
 "terms": [
  {"term": "Class histogram", "plain": "A count of live objects and their bytes, per class."},
  {"term": "Heap dump", "plain": "A file (HPROF format) with every object on the heap and every reference between them."},
  {"term": "Retained size", "plain": "The memory that would be freed if one object became unreachable."},
  {"term": "Dominator", "plain": "Object X dominates Y if every path from a GC root to Y goes through X."},
  {"term": "Native Memory Tracking", "plain": "The JVM's own accounting of the memory it uses, including outside the heap."},
  {"term": "Direct buffer", "plain": "A ByteBuffer whose bytes live outside the heap, freed after its small heap object is collected."},
  {"term": "Arena", "plain": "In the FFM API, the owner of off-heap memory that decides when it's freed."},
  {"term": "MaxDirectMemorySize", "plain": "The limit for direct buffers and automatic arenas. Defaults to the max heap."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate, in your own words, how you'd go from \"the program keeps growing\" to the line of code that leaks, for both kinds of leak.",
  "answer": "First I'd read the GC log, because it says which half of memory is growing. If the after-values of young pauses keep rising, it's the heap. A class histogram shows which classes pile up, and a heap dump opened in MAT shows who holds them: the dominator tree ranks objects by retained size, what would be freed if they went away, and the path to a GC root names the static field, the thread or the map. If the floor is flat but the process grows, it's outside the heap. I'd restart one instance with Native Memory Tracking, take a baseline, and diff it later to see which category grows: `Other` points at direct buffers or native code, `Thread` at threads that never end, `Class` or `Metaspace` at class loaders. Then I'd fix the lifetime in code, bound caches, close arenas, and set `MaxDirectMemorySize` so the next direct-buffer leak fails with a stack trace."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few details make leak hunting faster.\n\nA histogram is cheap enough to take twice. Take one, wait ten minutes under load, take another, and compare instance counts: the class whose count only goes up is your lead, even before you have a dump. `jcmd <pid> GC.class_histogram -all` skips the full GC and counts unreachable objects too, which helps when you can't afford the pause and misleads when you forget the flag.\n\nHeap dumps are large: about the size of the live heap, here 52 MB for 44 MB of leak. `GC.heap_dump -gz=1` compresses while writing. Writing a dump stops the JVM, so in a group of identical services, take it from one instance after you've stopped sending it traffic.\n\nMAT's GC roots have kinds, and the kind is a clue. A *System Class* root means a static field. A *Thread* root, \"a started, but not stopped, thread\" in MAT's words, means something reachable from a live thread: its stack or its thread-locals. *JNI Global* means native code is holding a reference.\n\nClass loader leaks look different from object leaks. Each reload of an application creates a new class loader with new classes. If anything from outside still references one object of an old class, for example a database driver registered in a global list, a `ThreadLocal` on a shared thread or a static cache in a library, the whole old class loader and every class it loaded stay in metaspace. NMT shows `Class` and `Metaspace` growing, and GC logs show collections with the cause `Metadata GC Threshold`. A service in production rarely reloads, but tools that reload code on every change, and long test suites, do.\n\nFinally, `jol-cli`, JOL's command-line version, can estimate how a heap dump's objects would lay out under other JVM settings. For a similar 50 MB dump full of 2 KB arrays, it estimated 1.3% less with compact object headers and 3.2% more without compressed references. A heap of big arrays gains little from smaller headers, as lesson 1 predicted."
 },
 "sources": [
  {"title": "The jcmd command, JDK 25 man page source", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md"},
  {"title": "Eclipse MAT help: dominator tree", "url": "https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/dominatortree.html"},
  {"title": "Eclipse MAT help: GC roots", "url": "https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/gcroots.html"},
  {"title": "JEP 454: Foreign Function & Memory API", "url": "https://openjdk.org/jeps/454"},
  {"title": "Arena source at jdk-25-ga: the four kinds of arena", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/foreign/Arena.java"}
 ]
}

def move_answer(q, to):
    """Put the correct option at index `to`, keeping the others in order."""
    right = q["options"].pop(q["answer"])
    q["options"].insert(to, right)
    q["answer"] = to


for q, to in zip(L["quiz"], [0, 2, 3, 1, 1]):
    move_answer(q, to)

(ROOT / "content/lessons/mem-07.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-07")
