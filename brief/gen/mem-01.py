import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/memory/src"
P = "java/workbench/memory/l01"
K = "kotlin/workbench/memory/l01"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :memory:demo -Pmain=workbench.memory.l01."


def demo(name, title_j=None, title_k=None):
    return {"lang": "java", "title": title_j or f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": title_k or f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


# Native Memory Tracking, JDK 25.0.5, -Xmx256m, 64 MiB direct buffer + 32 MiB Arena + 50 extra threads + 100 MB of arrays
FIGURE = """<svg viewBox="0 0 680 300" role="img" aria-label="One JDK 25 process started with -Xmx256m: the Java heap is 216 MB of the 388 MB the process committed; memory outside the heap, GC bookkeeping, the class archive, code cache, thread stacks and metaspace sit beside it">
<rect class="box-dim" x="10" y="10" width="660" height="280" rx="8"/>
<text class="t t-m" x="340" y="34" text-anchor="middle">one JVM process on JDK 25, -Xmx256m: 388 MB committed</text>
<rect class="box-a" x="30" y="50" width="290" height="220" rx="8"/>
<text class="t" x="175" y="130" text-anchor="middle">Java heap</text>
<text class="t-s" x="175" y="152" text-anchor="middle">the shared storage floor</text>
<text class="t-s" x="175" y="174" text-anchor="middle">216 MB committed</text>
<text class="t-s" x="175" y="196" text-anchor="middle">every object you new</text>
<text class="t-s t-a" x="175" y="250" text-anchor="middle">the only part -Xmx caps</text>
<rect class="box-b" x="340" y="50" width="310" height="62" rx="8"/>
<text class="t" x="495" y="78" text-anchor="middle">memory outside the heap</text>
<text class="t-s" x="495" y="98" text-anchor="middle">direct buffer + Arena: 96 MB</text>
<rect class="box" x="340" y="120" width="310" height="40" rx="8"/>
<text class="t-s" x="495" y="145" text-anchor="middle">GC bookkeeping: 45 MB</text>
<rect class="box" x="340" y="168" width="310" height="28" rx="8"/>
<text class="t-s" x="495" y="187" text-anchor="middle">shared class archive (CDS): 14 MB</text>
<rect class="box" x="340" y="202" width="150" height="28" rx="8"/>
<text class="t-s" x="415" y="221" text-anchor="middle">code cache: 7 MB</text>
<rect class="box" x="500" y="202" width="150" height="28" rx="8"/>
<text class="t-s" x="575" y="221" text-anchor="middle">71 stacks: 6 MB</text>
<rect class="box" x="340" y="238" width="150" height="32" rx="8"/>
<text class="t-s" x="415" y="259" text-anchor="middle">metaspace: 1 MB</text>
<rect class="box" x="500" y="238" width="150" height="32" rx="8"/>
<text class="t-s" x="575" y="259" text-anchor="middle">other: about 3 MB</text>
</svg>"""

OPENING = """Picture a big storage warehouse. Out on the shared floor, rows of shelves hold thousands of boxes. Each worker has a desk by the door, with a notepad that lists the shelf numbers of the boxes they're busy with. Every box carries a label that says what kind of box it is. In a back room, a filing cabinet keeps the plans for every kind of box the warehouse knows.

A running Java program is that warehouse. The last track ended with agents, code that rewrites classes, the plans, while the program runs. This track is about the boxes: the objects made from those plans, and the memory they live in.

Two surprises wait for anyone who measures. A program started with `-Xmx256m` can take 388 MB from the operating system. And a `Long`, which holds one 8-byte number, takes more than 8 bytes. Both are easy to miss, because the source code shows neither the warehouse nor the labels.

In this lesson, we'll walk through the warehouse, read the label on one box, and try two JVM settings that change its size. Before we start, make a guess, and keep it in mind."""

S1 = """Let's set up the example for the whole track. A small photo-sharing site runs a thumbnail service. When someone uploads a photo, the service makes a thumbnail, a small preview picture, and keeps recent thumbnails in memory so it can send them again without redoing the work. It's an ordinary program, and the JVM (the Java Virtual Machine, the program that runs your compiled Java and Kotlin) gives it memory in several separate areas.

The biggest area is the **heap**, the shared storage floor. Every object the service creates with `new` lives there: each thumbnail, its pixels, the strings for its file names. The **garbage collector** (GC) is the part of the JVM that finds objects nothing uses any more and reuses their memory. It's the warehouse's cleaning crew, and lesson 4 follows it at work. The `-Xmx` option, given when the program starts, sets the largest size the heap may grow to.

A thread is one path of work running through the program, and each thread is a worker with a desk. The desk is the thread's **stack**: the local variables, and the place to return to, of every method the thread is in the middle of. A local variable never holds an object itself. It holds a reference, the object's address on the heap, like a shelf number on the notepad. An ordinary thread is called a platform thread, because the operating system runs it, and its stack lives outside the heap.

The plans live in **metaspace**: the JVM's description of every class it has loaded, with its fields, its methods and their bytecode (the instructions the compiler wrote into the class file). Next to it sits the code cache. The JIT compilers, the parts of the JVM that turn busy bytecode into machine code while the program runs, keep their output there.

It's natural to read `-Xmx` as the size of the program. It isn't. Here's a JDK 25 program started with `-Xmx256m` and measured by Native Memory Tracking (NMT), the JVM's own accounting of its memory. The program holds 100 MB of arrays, 50 extra threads and 96 MB of memory outside the heap. Committed means memory the operating system has really handed over, as opposed to addresses only reserved for later:

| Area | Committed | What lives there |
|---|---|---|
| Java heap | 216 MB | every object you create with `new` |
| Memory outside the heap | 96 MB | `ByteBuffer.allocateDirect` and `Arena.allocate` (64 MB and 32 MB here) |
| GC bookkeeping | 45 MB | the collector's own records about the heap (lesson 4) |
| Shared class archive (CDS, class data sharing) | 14 MB | JDK classes, already parsed, read from a file |
| Code cache | 7 MB | machine code from the JIT compilers |
| Thread stacks | 6 MB | one stack per platform thread (71 of them) |
| Metaspace | 1 MB | the plans for the classes loaded from the program's own jars |

The process committed 388 MB, and 172 MB of it lives outside the heap, where `-Xmx` limits none of it. In the warehouse, `-Xmx` caps the storage floor. The desks (stacks), the filing room (metaspace) and the yard out back (memory outside the heap) come on top.

Three rows deserve a sentence each. Each platform thread reserves a 1 MB stack on Linux x64 but commits only the pages it touches, which is why 71 threads committed just 6 MB. Metaspace has no limit by default, so a program that keeps loading new classes keeps growing it. And a direct buffer is memory the program asks for outside the heap, often to read and write files and network data. The heap holds only a small object that points to it. `Arena.allocate`, from the Foreign Function and Memory API (final since JDK 22), hands out the same kind of memory. (A virtual thread is the one exception to "stacks live outside the heap": while it waits, its frames sit in ordinary objects on the heap, as the virtual threads track showed.)

Lesson 6 of this track fits all of these areas into a fixed memory budget, and lesson 7 measures them with NMT. For now, let's step onto the floor and look at one box."""

S2 = """`new Object()` has no fields at all, and it still takes 16 bytes of heap. Those bytes are the label. On a 64-bit HotSpot JVM (HotSpot is the JVM inside OpenJDK and most Java downloads), every object starts with a **header** of two parts.

The **mark word**, 8 bytes, is the housekeeping strip. It holds the object's identity hash code (the one `Object.hashCode()` returns when a class doesn't override it), once something asks for it. It holds the GC age: how many cleanings the object has survived, in 4 bits, so at most 15. And it holds the bits that `synchronized` uses when a thread locks the object.

The **class pointer**, 4 bytes by default, says what kind of box this is. It points to the class's plan in metaspace.

That's 12 bytes before the first field. After the fields comes padding: every object starts at a multiple of 8 bytes, so its size rounds up to the next multiple of 8. `new Object()` is 12 bytes of header plus 4 of padding. An `Integer` puts its 4-byte `int` where the padding would go, so it's 16 too. A `Long` needs 8 bytes for its value: 12 + 8 = 20, which rounds up to 24. That was the warm-up.

Here the warehouse picture breaks, and it's worth saying out loud. A paper label costs no shelf space. A Java header sits inside the box and takes 12 of its bytes, whether the box holds 4 bytes of data or 4,000.

Now the service's own class. A `Thumbnail` object carries a few facts about one preview picture, and a reference to its pixels:

```java
class Thumbnail {
    boolean cached;
    long createdAtMillis;
    byte format;          // 1 = JPEG, 2 = PNG
    String name;
    int width;
    byte[] pixels;
}
```

```kotlin
class Thumbnail {
    var cached = false
    var createdAtMillis = 0L
    var format: Byte = 0  // 1 = JPEG, 2 = PNG
    var name: String? = null
    var width = 0
    var pixels: ByteArray? = null
}
```

Kotlin compiles each `var` to the same JVM field as the Java line above it, so both classes get the same layout. JOL (Java Object Layout), a small OpenJDK tool, prints what the JVM really did with those fields. In its printout, OFF is each part's offset, its distance in bytes from the start of the object, and SZ is its size. This is JOL on JDK 25 with default settings:

```text
OFF  SZ               TYPE DESCRIPTION                 VALUE
  0   8                    (object header: mark)       N/A
  8   4                    (object header: class)      N/A
 12   4                int Thumbnail.width             N/A
 16   8               long Thumbnail.createdAtMillis   N/A
 24   1            boolean Thumbnail.cached            N/A
 25   1               byte Thumbnail.format            N/A
 26   2                    (alignment/padding gap)
 28   4   java.lang.String Thumbnail.name              N/A
 32   4             byte[] Thumbnail.pixels            N/A
 36   4                    (object alignment gap)
Instance size: 40 bytes
```

Read it from the top. The header fills offsets 0 to 11. Then the JVM, a tidy packer, did something the source never asked for. It moved `width` up to offset 12, into the 4 bytes after the header, because a `long` must start at a multiple of 8 and wouldn't fit there. The `long` follows at 16, then the two 1-byte fields, a 2-byte gap, and the two references at 4 bytes each. Four bytes of padding end the object at 40.

So 6 of the 40 bytes are gaps. They're room for later: a subclass that adds a `String` and a `short` still takes 40 bytes, because its fields slide into those gaps. The lab measures exactly that case.

You don't need JOL to estimate, though. **An object costs its header plus its fields, rounded up to 8. Count objects, not data.**

Counting objects is where the surprises live. The file extension `"jpg"` as a `String` costs 48 bytes, 16 bytes per letter: a 24-byte `String` object plus a 24-byte `byte[]` that holds the 3 letters. An `ArrayList<Integer>` with the numbers 0 to 999 costs 20,976 bytes, because each number is its own 16-byte `Integer` plus a 4-byte reference in the list. An `int[1000]` holds the same numbers in 4,016.

All of those references took 4 bytes. On a 64-bit machine, that should be impossible."""

S3 = """A reference on a 64-bit machine should take 8 bytes, the size of a full memory address. On HotSpot it usually takes 4, thanks to **compressed oops**. ("Oop" is HotSpot's name for an ordinary object pointer, which is what a reference is inside the JVM.)

The trick follows from the padding. Every object starts at a multiple of 8, so the lowest 3 bits of every object's address are always zero. The JVM doesn't store them. It stores a 32-bit number instead, and shifts it left by 3 bits (multiplies it by 8) whenever it follows the reference. In the warehouse, it's writing a short shelf number on the notepad instead of the full address, because every shelf slot is 8 bytes wide. A 32-bit number counts about 4 billion slots, and 4 billion slots of 8 bytes reach 32 GB.

So while the maximum heap is under 32 GB, every reference field and every slot of an `Object[]` takes 4 bytes. Give the JVM `-Xmx32g` or more, and it switches compressed oops off by itself. References go back to 8 bytes. These are JOL's numbers on JDK 25 with `-Xmx40g` (the JVM only reserves addresses for the maximum heap at start-up, so this runs on a small laptop):

| Object | heap under 32 GB | `-Xmx40g` |
|---|---|---|
| `Thumbnail` | 40 | 48 |
| `String` (the object alone) | 24 | 32 |
| `"jpg"` with its array | 48 | 56 |
| `ArrayList<Integer>` of 1,000 | 20,976 | 25,920 |
| `int[1000]` | 4,016 | 4,016 |

The list grew by 24%. That makes a 40 GB heap a strange deal. Moving from `-Xmx31g` to `-Xmx40g` buys 29% more heap, and the same objects grow by about a fifth, so longer references eat most of the new room. Bigger isn't always bigger. The `int[]` didn't change at all, because it holds numbers, not references.

There's a way past the cliff: `-XX:ObjectAlignmentInBytes=16`. With 16-byte slots, the same 32-bit numbers reach 64 GB. The price is that every object now pads to a multiple of 16, so a `Thumbnail` is 48 bytes again. I'd rather keep each JVM under 32 GB and run more of them.

The class pointer has its own compression, into a separate 1 GB space for class data. That's why the header stays at 12 bytes even when compressed oops are off. And since JDK 25, there's a supported way to make the header itself smaller."""

S4 = """Project Lilliput, the OpenJDK project working on smaller object headers, shrank the label to 8 bytes. With **compact object headers**, the class pointer moves into the mark word itself, squeezed into 22 bits, and the separate class word disappears. The flag changed status on the way, each step described in a JEP (a JDK Enhancement Proposal, the document behind each new JDK feature), so the version matters:

| JDK | Compact object headers |
|---|---|
| 21 | not there: the JVM stops with `Unrecognized VM option 'UseCompactObjectHeaders'` |
| 24 | experimental (JEP 450): `-XX:+UnlockExperimentalVMOptions -XX:+UseCompactObjectHeaders` |
| 25 and 26 | a product feature, off by default (JEP 519): `-XX:+UseCompactObjectHeaders` alone |
| 27 | on by default, per the JDK 27 source; `-XX:-UseCompactObjectHeaders` turns it off |

On JDK 25, then, it's one flag. Here's the thumbnail with it, printed by JOL and confirmed by the JVM's own allocation counter (10,000 thumbnails took 320,000 bytes):

```text
OFF  SZ               TYPE DESCRIPTION                 VALUE
  0   8                    (object header: mark)       N/A
  8   8               long Thumbnail.createdAtMillis   N/A
 16   4                int Thumbnail.width             N/A
 20   1            boolean Thumbnail.cached            N/A
 21   1               byte Thumbnail.format            N/A
 22   2                    (alignment/padding gap)
 24   4   java.lang.String Thumbnail.name              N/A
 28   4             byte[] Thumbnail.pixels            N/A
Instance size: 32 bytes
```

The fields now start at offset 8, so the `long` fits right after the header, and the object ends at exactly 32 bytes with no padding at the end.

The JDK 25 manual says the option saves "4 bytes per object (on average)". The word that matters is "average". Objects still round up to a multiple of 8, so each one saves either 8 bytes or nothing. These are JDK 25 measurements, without the flag and with it:

| Object | 12-byte header | 8-byte header |
|---|---|---|
| `new Object()` | 16 | 8 |
| `Thumbnail` | 40 | 32 |
| `Long` | 24 | 16 |
| `byte[3]` | 24 | 16 |
| `Integer` | 16 | 16 |
| `String` (the object alone) | 24 | 24 |

An `Integer` was 12 + 4 = 16, and is now 8 + 4 = 12, which rounds right back up to 16. So the `ArrayList<Integer>` from the last section, a thousand `Integer`s, saved nothing at all: still 20,976 bytes.

The saving follows the number of small objects, not the size of the heap. A heap full of small objects, map entries and boxed numbers gains the most; the million-entry map in the worked example below shrinks by 17%. A heap full of large arrays barely notices, because one array saves at most 8 bytes.

On JDK 25 it's worth a load test, because it's one flag and you can take it away again. So far we've only measured the boxes. How they get onto the floor, and how fast, is the next question."""

ASIDE = {
    "title": "Can compact headers break my program?",
    "body": "Ordinary Java and Kotlin code can't tell the difference: no field moves in any way your code can see. What can notice is code that reads object memory by hand at fixed offsets, through `sun.misc.Unsafe`, and assumes the first field sits at offset 12. With compact headers, it sits at 8. Old agents (the class-rewriting code from the last track), old serialization libraries and old off-heap tricks are the usual suspects, so run their tests with the flag on. JOL 0.17 is old too, but it asks the JVM for each field's real offset, which is why its printout above agrees with the allocation counter."
}

L = {
 "id": "mem-01",
 "title": "Where objects live: heap, stacks, metaspace and object headers",
 "minutes": 35,
 "goal": "By the end you can name the memory areas of a JVM process, predict the size of an object from its fields, and say what compressed references and compact object headers change.",
 "opening": OPENING,
 "warmup": {
  "q": "On a 64-bit JDK 25 with default settings, how many bytes of heap does one `Long` object take?",
  "options": ["8", "16", "24", "32"],
  "answer": 2,
  "why": "The `long` value is 8 bytes, but every object also starts with a 12-byte header: an 8-byte mark word and a 4-byte class pointer. 12 + 8 = 20, and objects round up to a multiple of 8, so a `Long` takes 24 bytes. 8 forgets the header. 16 is the size of an `Integer`, whose 4-byte value fits right after the header, and of a `Long` once you turn on compact object headers."
 },
 "sections": [
  {
   "h": "Where a running program keeps things: heap, stacks and metaspace",
   "body": S1,
   "figure": {"svg": FIGURE, "caption": "Native Memory Tracking for one JDK 25 process started with -Xmx256m: the heap was 216 MB of the 388 MB the process committed."},
   "try": {
    "title": "List the memory areas of a JVM",
    "minutes": 3,
    "steps": [
     "Read `MemoryAreasDemo` (or its Kotlin twin). It lists every memory pool the JVM reports, then asks for a 64 MiB direct buffer. Predict: will the buffer show up in one of the heap pools?",
     "Run it from the `labs/` folder with the command below.",
     "Compare the max heap it prints with your machine's memory. When you give no `-Xmx`, the JVM takes a quarter of it."
    ],
    "code": demo("MemoryAreasDemo"),
    "expect": "Three heap pools (`G1 Eden Space`, `G1 Survivor Space`, `G1 Old Gen`) and several non-heap ones: `Metaspace`, `Compressed Class Space` and three `CodeHeap` pools for compiled code. The 64 MB buffer appears in none of them, only in the `direct` buffer pool, because it lives outside the heap. The max heap is 25% of your memory, or of the memory limit the program runs under, if it has one: on the 13.4 GB machine behind this lesson, it printed 3,420 MB."
   },
   "refs": [
    {"title": "The java command, JDK 25 manual (source of the man page)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "The label on every box: a 12-byte header, the fields, then padding",
   "body": S2,
   "try": {
    "title": "Print real layouts with JOL",
    "minutes": 5,
    "steps": [
     "Before you run anything, write down your guess for a `Thumbnail`, an `Integer`, a `Long`, and the string `\"jpg\"` with its array.",
     "Run `LayoutDemo` (Java) or `LayoutDemoKt` (Kotlin, whose class is called `KThumbnail`). JOL prints a few warnings first: two about attaching an agent, and on JDK 25 four more about \"a terminally deprecated method in sun.misc.Unsafe\", because JOL 0.17 dates from 2023. The layouts are still right.",
     "Find the padding in the printout. Then read the last line: the JVM's own allocation counter, which measures the same thing without JOL."
    ],
    "code": demo("LayoutDemo"),
    "expect": "`Thumbnail` is 40 bytes, with a 2-byte gap in the middle and 4 bytes of padding at the end. Then `Object 16, Integer 16, Long 24, String shell 24 bytes`, and `\"jpg\"` with its array is 48. The `ArrayList<Integer>` of 0 to 999 costs 20,976 bytes against 4,016 for `int[1000]`. The last line says 10,000 thumbnails allocated 400,000 bytes, 40 per object: the same answer JOL gave."
   },
   "refs": [
    {"title": "JOL (Java Object Layout) on GitHub", "url": "https://github.com/openjdk/jol", "kind": "docs"}
   ]
  },
  {
   "h": "Short shelf numbers: compressed references up to 32 GB",
   "body": S3,
   "try": {
    "title": "Turn compressed oops off",
    "minutes": 4,
    "steps": [
     "Predict the new size of a `Thumbnail` and of the `ArrayList<Integer>` once every reference is 8 bytes.",
     "Run the demo again with `-Pargs=-XX:-UseCompressedOops` added to the command. The demo starts a child JVM with that flag.",
     "Run it once more with `-Pargs=-Xmx40g` instead, and compare the two printouts."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :memory:demo -Pmain=workbench.memory.l01.LayoutDemo -Pargs=-XX:-UseCompressedOops\n./gradlew :memory:demo -Pmain=workbench.memory.l01.LayoutDemo -Pargs=-Xmx40g", "run": ""},
    "expect": "Both runs print the same numbers. References are 8 bytes now, so `Thumbnail` grows to 48, and its gaps merge into one 6-byte gap before the first reference. The `String` object is 32, `\"jpg\"` is 56 and the list is 25,920 bytes, while `int[1000]` stays at 4,016. The allocation counter says 48 bytes per thumbnail. `-Xmx40g` switched compressed oops off all by itself."
   }
  },
  {
   "h": "A smaller label: compact object headers on JDK 25",
   "body": S4,
   "aside": ASIDE,
   "try": {
    "title": "Turn on compact headers",
    "minutes": 3,
    "steps": [
     "This step needs Gradle running on JDK 25 or later. Check the `Daemon JVM` line of `./gradlew --version`. On JDK 21 the child JVM stops with `Unrecognized VM option 'UseCompactObjectHeaders'`, which proves the first row of the version table.",
     "Predict the sizes of `Object`, `Long`, `Integer` and `\"jpg\"` with an 8-byte header. Then run the demo with `-Pargs=-XX:+UseCompactObjectHeaders`.",
     "Compare the last line, which the JVM measures itself, with the first run of this lesson."
    ],
    "code": {"lang": "bash", "title": "terminal (JDK 25)", "src": "./gradlew :memory:demo -Pmain=workbench.memory.l01.LayoutDemo -Pargs=-XX:+UseCompactObjectHeaders", "run": ""},
    "expect": "On JDK 25 the layout starts its fields at offset 8, and `Thumbnail` is 32 bytes. Then `Object 8, Integer 16, Long 16, String shell 24 bytes`, `\"jpg\"` with its array is 40 bytes, and the list of 1,000 `Integer`s is still 20,976. The counter reports 320,000 bytes for 10,000 thumbnails, 32 per object, against 40 without the flag. The line marked \"JOL simulation\" says 32 in every run, because it's a model, not a measurement."
   },
   "refs": [
    {"title": "JEP 519: Compact Object Headers", "url": "https://openjdk.org/jeps/519", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "The same two fields in Java and Kotlin",
  "java": {"title": "Photo.java", "src": "class Photo {\n    long sizeBytes;       // primitive: 8 bytes inside the object\n    Long takenAtMillis;   // reference: 4 bytes here, plus a 24-byte Long elsewhere (null when unknown)\n}"},
  "kotlin": {"title": "Photo.kt", "src": "class Photo(\n    var sizeBytes: Long,        // compiles to a long field: 8 bytes inside the object\n    var takenAtMillis: Long?,   // compiles to a java.lang.Long field: a reference plus a 24-byte box\n)"},
  "note": "Both classes compile to the same two JVM fields and the same 24-byte layout, and JOL can't tell them apart. The difference is what the source shows you. Java names the box: `Long` with a capital L is an object, `long` is not. Kotlin has one `Long` type and picks for you: a primitive `long` when it can, and a boxed `java.lang.Long` when the type is nullable (`Long?`) or a type argument (`List<Long>`). So in Kotlin, a single `?` can add an object per value. `val` versus `var` changes nothing in size, and `data class` adds methods, not fields."
 },
 "worked": {
  "title": "Estimate a million-entry map of upload ids, then check it",
  "steps": [
   {"say": "The thumbnail service remembers which uploads it has already processed, so a photo uploaded twice is only shrunk once. Each upload has an id, a random 36-character string (a UUID written as text), and the map goes from that id to the size of the stored thumbnail in bytes. How much heap does it take at a million entries?",
    "code": "// key: the upload's id, value: the thumbnail's size in bytes\nMap<String, Long> done = new HashMap<>();\ndone.put(upload.id(), thumbnailBytes);",
    "lang": "java",
    "alt_code": "// key: the upload's id, value: the thumbnail's size in bytes\nval done = HashMap<String, Long>()\ndone[upload.id] = thumbnailBytes",
    "alt_lang": "kotlin"},
   {"say": "1. List the objects one entry creates, and size each one with the rule: header plus fields, rounded up to 8. The map's table is shared by all entries. A million entries is more than 0.75 of 2^20 slots, so `HashMap` grows its table to 2^21 slots of 4 bytes, 8 MB in all.",
    "code": "String          24   header 12 + byte[] ref 4 + hash 4 + coder 1 + flag 1 = 22 -> 24\nbyte[36]        56   header 12 + length 4 + 36 bytes of letters = 52 -> 56\nLong            24   header 12 + long 8 = 20 -> 24\nHashMap$Node    32   header 12 + hash 4 + key, value, next 3 x 4 = 28 -> 32\ntable slot     ~8.4  2,097,152 slots x 4 bytes / 1,000,000 entries\n               ------\n               ~144 bytes per entry, ~144 MB for the map",
    "lang": "text"},
   {"say": "2. Check the estimate instead of trusting it. JOL's `GraphLayout` walks every object the map can reach. On JDK 25 with random ids, it counted 4,000,002 objects and 144,388,672 bytes: 144.4 per entry. The data itself is 36 + 8 = 44 bytes per entry, so two thirds of the map is labels, references and padding.",
    "code": "GraphLayout g = GraphLayout.parseInstance(done);\nSystem.out.println(g.toFootprint());     // a table: count and bytes per class\nSystem.out.println(g.totalSize() / done.size() + \" bytes per entry\");",
    "lang": "java",
    "alt_code": "val g = GraphLayout.parseInstance(done)\nprintln(g.toFootprint())                 // a table: count and bytes per class\nprintln(\"${g.totalSize() / done.size} bytes per entry\")",
    "alt_lang": "kotlin"},
   {"say": "3. Shrink it where the bytes are. The key costs 80 bytes as a `String` plus its array. A `UUID` object holds the same 128 bits in two `long` fields and takes 32 bytes. JOL then counts 96,388,672 bytes, 96.4 per entry: a third less. Compact headers on JDK 25 stack on top of that, with 120.4 bytes per entry for the string keys and 72.4 for `UUID` keys. Putting a limit on the map's size saves even more, and lesson 7 does that.",
    "code": "Map<UUID, Long> done = new HashMap<>();\ndone.put(UUID.fromString(upload.id()), thumbnailBytes);   // a 32-byte key instead of 80",
    "lang": "java",
    "alt_code": "val done = HashMap<UUID, Long>()\ndone[UUID.fromString(upload.id)] = thumbnailBytes        // a 32-byte key instead of 80",
    "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Predict object sizes, then check them against JOL",
  "minutes": 12,
  "files": [
   "labs/memory/src/main/java/workbench/memory/l01/ObjectSize.java",
   "labs/memory/src/test/java/workbench/memory/l01/Samples.java"
  ],
  "run": "./gradlew :memory:test --tests 'workbench.memory.l01.*'",
  "steps": [
   "Run the tests once. All 8 fail with `UnsupportedOperationException`. Open `Samples.java` in the test folder: these are the classes the tests measure, starting with the lesson's `Thumbnail`.",
   "Write `alignUp`. The alignment is always a power of two.",
   "Write `fieldBytes`: the eight primitive widths, and `vm.referenceBytes()` for everything else, arrays included.",
   "Write `instanceSize`: start at the header size, add every non-static field of the class and of each superclass, and round up. Then write `arraySize`: the header, 4 bytes of length, the elements, rounded up.",
   "Run the tests until all 8 pass. The last test builds a `Vm` from JOL's view of the JVM that runs the tests, and compares your answers with JOL's for nine classes and three arrays."
  ],
  "hints": [
   "`(size + alignment - 1) / alignment * alignment` rounds up. The solution uses the bit trick `(size + alignment - 1) & -alignment`, which only works for powers of two.",
   "`Modifier.isStatic(field.getModifiers())` tells you to skip a field. `Class.getSuperclass()` returns `null` after `Object`.",
   "`type.isPrimitive()` is false for `Integer.class` and for `int[].class`. Both are references when they appear as a field.",
   "`WatermarkedThumbnail` adds a `String` and a `short` to `Thumbnail` and still takes 40 bytes. Summing the fields gets that right: 12 + 22 + 6 = 40, the size the padding had already reached."
  ],
  "done_when": "All 8 tests in `ObjectSizeTest` pass."
 },
 "drill": {
  "title": "Size an object in your head",
  "minutes": 4,
  "prompt": "Close the page. Work out the size of `class Crop { long sizeBytes; int width; boolean square; String name; }` three ways: default settings, without compressed oops, and with compact headers. Then write `alignUp` from memory.",
  "answer": {
   "lang": "java",
   "src": "// Crop { long sizeBytes; int width; boolean square; String name; }\n// default:            12 + 8 + 4 + 1 + 4 = 29 -> 32 bytes\n// no compressed oops: 12 + 8 + 4 + 1 + 8 = 33 -> 40 bytes\n// compact headers:     8 + 8 + 4 + 1 + 4 = 25 -> 32 bytes (padding eats the saving)\nstatic long alignUp(long size, int alignment) {\n    return (size + alignment - 1) / alignment * alignment;\n}",
   "alt": {
    "lang": "kotlin",
    "src": "// class Crop(var sizeBytes: Long, var width: Int, var square: Boolean, var name: String)\n// default:            12 + 8 + 4 + 1 + 4 = 29 -> 32 bytes\n// no compressed oops: 12 + 8 + 4 + 1 + 8 = 33 -> 40 bytes\n// compact headers:     8 + 8 + 4 + 1 + 4 = 25 -> 32 bytes (padding eats the saving)\nfun alignUp(size: Long, alignment: Int): Long =\n    (size + alignment - 1) / alignment * alignment"
   }
  }
 },
 "recap": [
  "`-Xmx` caps only the heap, the shared storage floor. Thread stacks, metaspace, the code cache, GC bookkeeping and memory outside the heap come on top: 172 MB on top of a 216 MB heap in one JDK 25 process.",
  "Every object starts with a header: an 8-byte mark word (hash code, GC age, lock bits) and a 4-byte class pointer, 12 bytes by default on JDK 21 to 26.",
  "Size = header + fields, rounded up to 8: `Integer` 16, `Long` 24, `Thumbnail` 40. A small new field can fill the padding for free. Count objects, not data.",
  "Compressed oops keep references at 4 bytes while the max heap is under 32 GB. From `-Xmx32g` up they switch off, and the same objects grow by about a fifth.",
  "Compact object headers (8 bytes) are one flag on JDK 25, `-XX:+UseCompactObjectHeaders`, and the default on JDK 27. Each object saves 8 bytes or nothing, so the gain follows your count of small objects.",
  "The limit of today's tools: JOL and the allocation counter tell you what objects cost. They say nothing about how long objects live, and lifetime is what the garbage collector pays for."
 ],
 "closing": """We started in a warehouse with a shared floor, desks by the door and a label on every box. The JVM has the same parts: a heap that `-Xmx` caps, with stacks and metaspace beside it. Inside every object sits a label of 12 bytes, or 8 with compact headers on JDK 25.

Now look in your own code for a map or list that holds millions of small things, such as a `Map<String, Long>`. Count the objects in one entry, not the data.

Next, we'll put new boxes on the floor. Creating an object takes a handful of machine instructions, and sometimes none at all. How does the JVM find room so fast, and when does it skip the box entirely?""",
 "quiz": [
  {
   "q": "What is the shallow size (the object alone, without what it points to) of `class Size { long bytes; int width; }` on JDK 25 with default settings?",
   "options": ["12 bytes", "16 bytes", "24 bytes", "32 bytes"],
   "answer": 2,
   "why": "A 12-byte header + 8 + 4 = 24, which is already a multiple of 8. The JVM puts the `int` at offset 12, right after the header, and the `long` at 16. 12 forgets the header. 32 assumes a 16-byte header, which you only get with compressed class pointers switched off."
  },
  {
   "q": "A batch job holds a large in-memory map of photo records. A teammate raises `-Xmx` from 30g to 36g to fit 20% more records. What happens?",
   "options": [
    "Compressed oops switch off, every reference doubles, and the extra 6 GB holds far fewer records than planned",
    "It fits 20% more records, because heap size and capacity grow together",
    "The JVM refuses to start, because compressed oops can't address 36 GB",
    "Nothing changes until the heap is full"
   ],
   "answer": 0,
   "why": "At 32 GB and above the JVM stops compressing references, so every reference field and array slot grows from 4 to 8 bytes. On JOL's numbers the same objects grow by about a fifth, which eats most of the extra 6 GB. The JVM still starts: it simply picks 8-byte references on its own."
  },
  {
   "q": "Which of these objects gets smaller when you turn on compact object headers on JDK 25?",
   "options": ["An `Integer`", "A `Long`", "A `String` object (without its array)", "A `byte[1_000_000]`, by a meaningful amount"],
   "answer": 1,
   "why": "A `Long` is 12 + 8 = 20, padded to 24. With an 8-byte header it is 8 + 8 = 16 exactly, and the lesson's run measured 16. An `Integer` is 16 either way (12 + 4 = 16, and 8 + 4 = 12 pads back to 16). A `String` object stays 24 for the same reason. A one-megabyte array saves at most 8 bytes, which is nothing next to its data."
  },
  {
   "q": "A program started with `-Xmx512m` calls `ByteBuffer.allocateDirect(64 * 1024 * 1024)`. Where do those 64 MB live?",
   "options": ["In the young generation", "In the old generation", "In metaspace", "In native memory outside the heap"],
   "answer": 3,
   "why": "A direct buffer is memory outside the heap. The heap only holds a small `DirectByteBuffer` object that points to it. That's why the demo showed the buffer in the `direct` buffer pool and in no heap pool, and why `-Xmx` does not limit it. Metaspace holds the plans of classes, not buffers."
  },
  {
   "q": "From the virtual threads track: a virtual thread waiting for a slow web service to answer has unmounted from its carrier. Where are its stack frames now?",
   "options": [
    "Still on the carrier's stack, which stays reserved for it",
    "In a 1 MB thread stack outside the heap",
    "In stack chunk objects on the Java heap",
    "In metaspace, next to the class data"
   ],
   "answer": 2,
   "why": "When a virtual thread unmounts, the JDK copies its frames into stack chunk objects on the heap, sized to the frames that exist. The garbage collector manages them like any other object. The carrier's stack is free for the next virtual thread, and only platform threads get a fixed stack outside the heap.",
   "from": "vt-02"
  }
 ],
 "flashcards": [
  {"front": "How big is an object header on a 64-bit JDK 25 with default settings?", "back": "12 bytes: an 8-byte mark word and a 4-byte compressed class pointer."},
  {"front": "What does the mark word hold?", "back": "The identity hash code (once something asks for it), the GC age in 4 bits, and the lock bits."},
  {"front": "How many bytes does a `Long` take by default?", "back": "24: a 12-byte header plus 8 bytes of value is 20, rounded up to a multiple of 8."},
  {"front": "Up to which max heap do compressed oops work by default?", "back": "Just under 32 GB: about 4 billion 32-bit slot numbers times 8-byte slots. From `-Xmx32g` up, references take 8 bytes."},
  {"front": "Does `-Xmx` limit thread stacks, metaspace or direct buffers?", "back": "No. It caps only the Java heap. Everything else comes on top of it."},
  {"front": "How do you turn on compact object headers on JDK 25?", "back": "`-XX:+UseCompactObjectHeaders` on its own. It's a product feature in JDK 25, experimental in JDK 24, and the default in JDK 27."},
  {"front": "Why can adding a field to a class cost 0 bytes?", "back": "Objects round up to a multiple of 8. A small new field can fill the padding: the 40-byte `Thumbnail` plus a `String` and a `short` is still 40 bytes."}
 ],
 "terms": [
  {"term": "Heap", "plain": "The shared memory where every object created with `new` lives, and that the garbage collector cleans."},
  {"term": "Thread stack", "plain": "A thread's own memory for the local variables of the methods it is running. Outside the heap for platform threads."},
  {"term": "Metaspace", "plain": "Memory outside the heap for class metadata: fields, methods, bytecode. Unlimited by default."},
  {"term": "Object header", "plain": "The bytes at the start of every object: the mark word plus the class pointer, 12 bytes by default."},
  {"term": "Mark word", "plain": "The first 8 bytes of every object: hash code, GC age and lock bits."},
  {"term": "Compressed oops", "plain": "4-byte references that the JVM multiplies by 8 to reach up to 32 GB of heap."},
  {"term": "Shallow size", "plain": "The bytes of one object alone: header, fields and padding, not the objects it points to."},
  {"term": "Compact object headers", "plain": "An 8-byte header with the class pointer folded into the mark word. One flag on JDK 25, the default on JDK 27."}
 ],
 "explain_back": {
  "prompt": "A teammate is surprised that a `HashMap<String, Long>` holding a million upload ids takes about 144 MB, when the ids and the sizes add up to about 44 MB. Explain in your own words where the other 100 MB goes.",
  "answer": "An entry isn't 44 bytes of data. It's four objects, and every object pays a 12-byte header and rounds up to a multiple of 8. The id is a 24-byte `String` that points to a separate 56-byte `byte[]` with the 36 letters. The size is a 24-byte `Long` box around 8 bytes of value. The map adds a 32-byte `HashMap$Node` per entry, plus about 8 bytes of table slot. That makes about 144 bytes per entry, and JOL measured 144.4. To shrink it, store fewer objects: a `UUID` key (32 bytes) instead of a `String`, compact object headers on JDK 25, or a limit on the map's size."
 },
 "deeper": {
  "minutes": 10,
  "body": "The mark word has an exact bit layout, and it changed between JDK 21 and 25. On JDK 21 a normal object's mark word is `unused:25 hash:31 unused_gap:1 age:4 unused_gap:1 lock:2`. On JDK 25 it is `unused:22 hash:31 unused_gap:4 age:4 self-fwd:1 lock:2`, and with compact headers the 22 unused bits become `klass:22`, the class pointer. 22 bits can name about 4 million classes, which is plenty. The JDK 25 source marks four of the gap bits as reserved for Valhalla, the project that will bring value objects.\n\nYou can watch the word change with JOL's `ClassLayout.parseInstance(obj).toPrintable()`. On JDK 25 a fresh object shows `0x0000000000000001 (non-biasable; age: 0)`. After `System.identityHashCode(obj)`, the hash appears inside the word: `0x000002bc2ae4d001 (hash: 0xbc2ae4d0; age: 0)`. Inside a `synchronized` block the word became `0x000002bc2ae4d000`: the same bits with the last two changed from `01` to `00`. JOL 0.17 labels that a \"thin lock\" with an address, a name from older JDKs. On JDK 25 the JVM's lightweight locking is the default, so the word keeps its hash and the locking thread records the object on its own small lock stack. With `-XX:+UseCompactObjectHeaders`, JOL prints only the mark word, such as `0x0017280000000001 (Lilliput)`, with the class bits in its top part.\n\nField packing has its own rules since JDK 15. The JVM fills the 4-byte gap after a 12-byte header with an `int`, a `float` or a reference, but never with a `long`, which must start at a multiple of 8. That's why a `Long` has 4 bytes of padding in the middle and an `Integer` has none. Subclass fields can fill gaps left by the superclass, as the lab's `WatermarkedThumbnail` shows.\n\nTwo practical notes about JOL. On JDK 21 it can't read record field offsets unless you set `-Djol.magicFieldOffset=true` (the lab's test sets it in code before JOL starts). And without permission to attach to processes it prints warnings and guesses addresses, but the layouts and sizes it prints are still exact."
 },
 "sources": [
  {"title": "The java command (JDK 25 man page source): compressed oops and compact headers", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "markWord.hpp at jdk-25-ga: the mark word bit layout", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/markWord.hpp"},
  {"title": "JEP 519: Compact Object Headers", "url": "https://openjdk.org/jeps/519"},
  {"title": "JOL (Java Object Layout)", "url": "https://github.com/openjdk/jol"}
 ]
}

(ROOT / "content/lessons/mem-01.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-01")
