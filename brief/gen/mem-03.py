import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/memory/src"
P = "java/workbench/memory/l03"
K = "kotlin/workbench/memory/l03"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :memory:demo -Pmain=workbench.memory.l03."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIGURE = """<svg viewBox="0 0 680 290" role="img" aria-label="From the GC roots, a plain reference keeps a thumbnail alive; a SoftReference holds a decoded photo until memory is short; a WeakReference holds a plugin listener until the next GC; a PhantomReference only reports that a native buffer's owner is gone">
<rect class="box-a" x="16" y="105" width="124" height="80" rx="8"/>
<text class="t" x="78" y="140" text-anchor="middle">GC roots</text>
<text class="t-s" x="78" y="160" text-anchor="middle">stacks, statics</text>
<line class="ln" x1="140" y1="145" x2="186" y2="48" marker-end="url(#arr)"/>
<line class="ln" x1="140" y1="145" x2="186" y2="112" marker-end="url(#arr)"/>
<line class="ln" x1="140" y1="145" x2="186" y2="178" marker-end="url(#arr)"/>
<line class="ln" x1="140" y1="145" x2="186" y2="244" marker-end="url(#arr)"/>
<rect class="box" x="190" y="28" width="160" height="40" rx="8"/>
<text class="t" x="270" y="53" text-anchor="middle">plain field</text>
<rect class="box" x="190" y="92" width="160" height="40" rx="8"/>
<text class="t" x="270" y="117" text-anchor="middle">SoftReference</text>
<rect class="box" x="190" y="158" width="160" height="40" rx="8"/>
<text class="t" x="270" y="183" text-anchor="middle">WeakReference</text>
<rect class="box" x="190" y="224" width="160" height="40" rx="8"/>
<text class="t" x="270" y="249" text-anchor="middle">PhantomReference</text>
<line class="ln" x1="350" y1="48" x2="386" y2="48" marker-end="url(#arr)"/>
<line class="ln-d" x1="350" y1="112" x2="386" y2="112" marker-end="url(#arr)"/>
<line class="ln-d" x1="350" y1="178" x2="386" y2="178" marker-end="url(#arr)"/>
<line class="ln-d" x1="350" y1="244" x2="386" y2="244" marker-end="url(#arr)"/>
<rect class="box-ok" x="390" y="28" width="140" height="40" rx="8"/>
<text class="t" x="460" y="53" text-anchor="middle">thumbnail</text>
<rect class="box-b" x="390" y="92" width="140" height="40" rx="8"/>
<text class="t" x="460" y="117" text-anchor="middle">decoded photo</text>
<rect class="box-b" x="390" y="158" width="140" height="40" rx="8"/>
<text class="t" x="460" y="183" text-anchor="middle">plugin listener</text>
<rect class="box-dim" x="390" y="224" width="140" height="40" rx="8"/>
<text class="t" x="460" y="249" text-anchor="middle">native buffer</text>
<text class="t-s" x="605" y="52" text-anchor="middle">never collected</text>
<text class="t-s" x="605" y="116" text-anchor="middle">cleared before OOM</text>
<text class="t-s" x="605" y="182" text-anchor="middle">cleared at next GC</text>
<text class="t-s" x="605" y="248" text-anchor="middle">get() is always null</text>
</svg>"""

OPENING = """Back in the warehouse, a cleaning crew keeps the floor from filling up. The crew never asks the workers which boxes they still need, since the workers would say "all of them". Instead it starts at the desks and at the noticeboard by the door. It follows every shelf number written on a note, then every note found inside those boxes, and keeps whatever it reaches. Everything else goes.

Most days that's exactly right. Then the thumbnail service caches its decoded photos behind a `SoftReference`, which sounds like "keep it if there's room", and the whole cache empties at once on the busiest afternoon of the year. Or a `WeakHashMap` that should forget finished uploads grows all day.

Both traps are easy to fall into, because the names promise more than the contracts. In the last lesson, every box went onto the floor in a few instructions; this one asks when the crew may take it away. We'll follow the crew's notes from the start, try the three looser holds Java offers, and write a cleanup that really runs. Before we start, make a guess, and keep it in mind."""

S1 = """The garbage collector doesn't free the objects you stopped using. It frees the objects nothing can reach. It starts from the **GC roots**, the places where a running program holds references directly, not inside another object. The roots are the local variables on every live thread's stack (the desks) and the static fields (the noticeboard by the door). References held by native code (code written in a language such as C, which Java calls through JNI, the Java Native Interface) count as roots too. From the roots the collector follows every reference, and keeps whatever it finds. Everything else is garbage.

That rule ignores how many references point at an object. A box that nobody's note leads to is garbage, even if a hundred other forgotten boxes point at it.

The package `java.lang.ref` lets you point at an object without holding it as tightly as an ordinary reference does. A reference object, such as a `SoftReference`, points at another object, called its referent, and `get()` returns the referent while it's still there. The package's documentation defines a ladder, from the firmest hold to none:

- An object is **strongly reachable** if a chain of ordinary references leads to it. The GC leaves it alone.
- It is **softly reachable** if the only way to it goes through a `SoftReference`: "keep it if there's room". The GC may clear that reference when memory gets tight.
- It is **weakly reachable** if the only way goes through a `WeakReference`: "keep it only while someone else holds it". The next collection that finds it clears the reference.
- It is **phantom reachable** if only a `PhantomReference` is left. Its `get()` always returns `null`; it only tells you, afterwards, that the object is gone.
- Otherwise it's unreachable, and its memory can be reused.

Each reference object can carry a ReferenceQueue, a tray where the collector drops the slip. "Some time after" the GC sees the object drop to that rung, it clears the reference and puts it on the queue. That's the specification's own wording, and it promises no deadline:

```java
ReferenceQueue<byte[]> queue = new ReferenceQueue<>();
WeakReference<byte[]> weak = new WeakReference<>(new byte[1_000], queue);
System.gc();                              // a request, fine in a demo
Reference<?> gone = queue.remove(500);    // the same weak reference, once the GC cleared it
```

```kotlin
val queue = ReferenceQueue<ByteArray>()
val weak = WeakReference(ByteArray(1_000), queue)
System.gc()                               // a request, fine in a demo
val gone = queue.remove(500)              // the same weak reference, once the GC cleared it
```

Here the warehouse picture breaks, and the break matters for everything in this lesson. A real cleaning crew comes on a schedule. The JVM's crew comes when the heap needs room: many times a second on a busy service, and perhaps not for an hour on a quiet one. Nothing on the ladder says *when*.

**The GC frees what the roots can't reach, at a time it chooses. Never plan around that time.**

That missing "when" is the whole story of the first rung below strong."""

S2 = """`SoftReference` sounds made for caches, and its Javadoc says so: "Soft references are most often used to implement memory-sensitive caches." The contract is thinner than it sounds. The JVM guarantees one thing: every soft reference to a softly reachable object is cleared before it throws an `OutOfMemoryError`, the error that means the heap has no room left. Otherwise, in the Javadoc's words, "no constraints are placed upon the time" of clearing. HotSpot ties it to a flag, `-XX:SoftRefLRUPolicyMSPerMB` (default 1000), described as the "number of milliseconds per MB of free space in the heap" that an unused soft referent may live.

So let's squeeze one. The thumbnail service decodes photos before it shrinks them, and a decoded photo is big. Here a 64 MB heap keeps one 40 MB decoded photo behind a soft reference, and then the service decodes a second one of the same size. This is the GC log on JDK 25, cut to the lines that matter:

```text
beach photo cached: true
GC(5) Pause Full (G1 Compaction Pause) 42M->42M(64M) 5.464ms
GC(6) Pause Full (G1 Compaction Pause) 42M->1M(64M) 5.325ms
after decoding a 40 MB dog photo: beach photo cached: false
```

G1, the JVM's default collector, ran a **full GC**, a collection of the whole heap with every thread stopped, and it kept the soft referent. There was still no room, so G1 ran a second full GC that cleared the soft reference, and the new photo fit. The cached photo is gone, and the next request for it has to decode it again.

That's the trouble with soft caches in a service. A soft cache keeps your things right up to the moment you need them most. It empties in bulk, when the heap is nearly full and the collector is already running full GCs. Then every request that misses the cache rebuilds its entry at the same moment, on a machine that is slow for the same reason. And a heap full of soft references always looks full, so you can't size it by watching it.

Use a cache with an explicit size limit and an expiry time instead, and size the heap to hold it. Lesson 7 builds one. I'd keep soft references for data that is truly optional and cheap to rebuild, and decoded photos are neither.

Soft references hold on too long and let go all at once. Weak references have the opposite problem, and one job they do perfectly."""

S3 = """A weak reference holds nothing up. Once only weak references lead to an object, the next GC that finds it clears all of them at once. In the research behind this course, a short loop of GC requests cleared a weak reference on every run, under every collector it tried.

That makes weak references wrong for caches: a weakly held value lasts until the next GC, which on a busy service is milliseconds away. It makes them right for one job: attaching data to an object whose lifetime someone else controls, without making that object live any longer.

`WeakHashMap` is that idea as a map. Its keys are weak and its values are strong. When a key becomes unreachable, its entry disappears the next time you call `size()`, `get()` or `put()`. Here the service keeps a small preview record for each photo it knows about:

```java
Map<Photo, Preview> previews = new WeakHashMap<>();
previews.put(beach, new Preview(160));
beach = null;               // the photo is deleted; after a GC, previews.size() is 0
```

```kotlin
val previews = WeakHashMap<Photo, Preview>()
previews[beach] = Preview(160)
// once the photo is unreachable, the entry goes after the next GC
```

There's one trap, and the `WeakHashMap` Javadoc warns about it: a value must not refer to its own key. Suppose the map holds a `Thumbnail` value that keeps a reference to its source `Photo`. The map's strong value now holds the weak key strongly, so the key never becomes weakly reachable, and the entry never goes away. The demo below fills two maps and shows one emptying and the other stuck.

The same idea gives you a listener registry that doesn't leak. The thumbnail service lets plugins, such as a watermarker or a statistics counter, register to hear about each finished thumbnail. A registry that keeps its listeners in a plain list keeps every plugin alive, plus everything each plugin refers to, until someone remembers to unregister it. Hold them through `WeakReference` instead, and a plugin whose owner is gone simply disappears from the list.

The catch is the mirror image. A lambda registered inline, with no other reference to it anywhere, disappears too, at the next GC. It was a very short registration. Whoever owns a listener must keep a reference to it. The lab builds this registry.

The last rung, phantom, holds nothing at all. Its only job is to say when an object is gone, so that something outside the heap can be cleaned up."""

S4 = """Some objects own something the GC can't see. The service's image decoder, a native library written in C, hands out buffers of native memory, outside the heap, and each one must be given back exactly once. When the Java object that owns a buffer becomes garbage, the GC frees the object. The native memory stays taken, unless some code runs to free it.

`finalize()` was the first way to run code when an object died. Java 9 deprecated it, and since JDK 18 it has been deprecated for removal (JEP 421, the JDK Enhancement Proposal behind that step). A finalizer can bring its own object back to life. Finalizers run on one JVM thread, in no set order and at no set time. And an object with a finalizer needs at least two collections before its memory is freed. You can check whether your program still depends on one: start it with `--finalization=disabled` (JDK 18 and later), and no finalizer runs. In the demo on JDK 25, 1,000 objects with a finalizer ran 1,000 finalizers by default and 0 with the flag.

The replacement is `java.lang.ref.Cleaner`, built on phantom references. You register an object with a cleaning action. When the object becomes phantom reachable, the cleaner's thread runs the action. That thread is patient and literal: it runs the action when the slip arrives, and not a moment before. `register` returns a `Cleanable`, and its `clean()` runs the action at most once and unregisters it:

```java
public final class NativeBuffer implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();       // one thread for all buffers
    private final Cleaner.Cleanable cleanable;

    public NativeBuffer(NativeMemory memory, int bytes) {
        long handle = memory.allocate(bytes);
        cleanable = CLEANER.register(this, new Release(memory, handle));
    }

    private record Release(NativeMemory memory, long handle) implements Runnable {
        public void run() { memory.free(handle); }                 // no reference to the buffer
    }

    @Override public void close() { cleanable.clean(); }           // the normal path, safe to call twice
}
```

```kotlin
class NativeBuffer(memory: NativeMemory, bytes: Int) : AutoCloseable {
    private val cleanable: Cleaner.Cleanable

    init {
        val handle = memory.allocate(bytes)
        cleanable = CLEANER.register(this, Release(memory, handle))
    }

    // a nested class has no reference to the outer object; only an `inner` class does
    private class Release(val memory: NativeMemory, val handle: Long) : Runnable {
        override fun run() = memory.free(handle)
    }

    override fun close() = cleanable.clean()                       // the normal path, safe to call twice

    companion object { private val CLEANER: Cleaner = Cleaner.create() }
}
```

Read the constructor in order. It takes a handle from the native library, then registers `this` with the cleaner, together with a small `Release` object that holds only the library and the handle. `close()` doesn't free anything itself. It asks the `Cleanable` to run `Release` now, and a second `close()` finds nothing left to run.

**The cleaning action must not refer to the object it cleans.** If it does, the object never becomes phantom reachable, and the action never runs. A lambda that reads a field captures `this`: in `() -> memory.free(handle)`, `handle` means `this.handle`. A non-static inner class in Java captures `this` too. The `Cleaner` Javadoc warns about both.

And the cleaner is only a safety net. It runs some time after a GC, and maybe not at all before the JVM exits. Release resources with try-with-resources (`use {}` in Kotlin), and let the cleaner catch the ones somebody forgot. The lab hands you a `NativeBuffer` that breaks the rule in bold, and a registry that holds on too tightly."""

ASIDE = {
    "title": "Is it safe to call System.gc()?",
    "body": "It's a request, not a command. Its Javadoc promises nothing about how much it reclaims or when, `-XX:+DisableExplicitGC` turns it into nothing at all, and some collectors run it alongside the program instead of stopping it. This lesson uses it only in demos, and in test helpers that keep asking until a `ReferenceQueue` delivers and give up after a few seconds. Never put it in service code."
}

L = {
 "id": "mem-03",
 "title": "Reachability: strong, soft, weak and phantom references",
 "minutes": 37,
 "goal": "By the end you can say when the GC clears each kind of reference, pick the right one (or none) for caches, listeners and native resources, and write a Cleaner that really runs.",
 "opening": OPENING,
 "warmup": {
  "q": "The thumbnail service caches decoded watermark pictures as `Map<String, WeakReference<Picture>>`. Nothing else refers to the pictures. How long does a cached picture survive under normal load?",
  "options": ["Until memory runs low", "Until the next garbage collection that finds it", "Until the map entry is removed", "For the lifetime of the JVM"],
  "answer": 1,
  "why": "A weak reference doesn't keep its object alive. Once only weak references point to the picture, the next GC that finds it clears them, which on a busy service can be milliseconds after it was cached. \"Until memory runs low\" describes soft references. The map entry stays, but it holds an empty reference."
 },
 "sections": [
  {
   "h": "Following the notes: GC roots and the reachability ladder",
   "body": S1,
   "figure": {"svg": FIGURE, "caption": "Each kind of reference is a weaker rung on the ladder: the GC clears soft ones under memory pressure, weak ones at the next collection that finds them, and phantom ones only report that the object is gone."},
   "aside": ASIDE,
   "try": {
    "title": "Climb down the ladder",
    "minutes": 3,
    "steps": [
     "Read `ReferenceLadderDemo` (or the Kotlin twin). It makes four 1,000-byte arrays: one held strongly, one softly, one weakly and one through a phantom reference. Predict which survive a `System.gc()`, and which references land on the queue.",
     "Run it with the command below."
    ],
    "code": demo("ReferenceLadderDemo"),
    "expect": "Before the GC: soft `true`, weak `true`, and `phantom.get()` is `null` (it always is). After it: soft is still `true`, because memory isn't tight, and weak is `false`. The queue receives the `WeakReference` and the `PhantomReference`. The strong array is untouched."
   },
   "refs": [
    {"title": "java.lang.ref package docs at jdk-25-ga: the reachability definitions", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/package-info.java", "kind": "docs"}
   ]
  },
  {
   "h": "Keep it if there's room: soft references and memory pressure",
   "body": S2,
   "try": {
    "title": "Squeeze a soft cache",
    "minutes": 3,
    "steps": [
     "Read `SoftCacheDemo`. It starts a child JVM with `-Xmx64m -Xlog:gc`, keeps a 40 MB decoded photo behind a soft reference, then decodes a second 40 MB photo. Predict: does the second allocation fail?",
     "Run it and read the GC lines between the two printouts."
    ],
    "code": demo("SoftCacheDemo"),
    "expect": "No `OutOfMemoryError`. Between the two printouts, on JDK 25, you'll see `Pause Full (G1 Compaction Pause) 42M->42M(64M)`, which kept the soft referent, then a second `Pause Full (G1 Compaction Pause) 42M->1M(64M)`, which cleared it. The last line says the beach photo is no longer cached. Two full GCs to empty one cache is the cost a soft cache hides."
   },
   "refs": [
    {"title": "SoftReference source at jdk-25-ga: the clearing contract", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/SoftReference.java", "kind": "docs"}
   ]
  },
  {
   "h": "Keep it while someone else holds it: weak references and WeakHashMap",
   "body": S3,
   "try": {
    "title": "Watch a WeakHashMap empty, and one that doesn't",
    "minutes": 3,
    "steps": [
     "Read `WeakHashMapDemo`. Both maps get one entry, and both photos are dropped. Only the `Thumbnail` value refers back to its key.",
     "Predict both sizes, then run it."
    ],
    "code": demo("WeakHashMapDemo"),
    "expect": "`previews left: 0` and `thumbnails left: 1`. The thumbnail holds its `Photo` strongly, so the weak key never becomes weakly reachable. That entry will stay for as long as the map does."
   }
  },
  {
   "h": "Tell me after it's gone: Cleaner, phantom references and the end of finalize",
   "body": S4,
   "try": {
    "title": "Switch finalization off",
    "minutes": 3,
    "steps": [
     "Read `FinalizerDemo`. It creates 1,000 objects whose class overrides `finalize()`, asks for 20 GCs, and counts the finalizer calls, once with default flags and once with `--finalization=disabled`.",
     "Run it. Then think of one library your own code uses that might still have a finalizer, and how you'd test without it."
    ],
    "code": demo("FinalizerDemo"),
    "expect": "`finalized 1000 of 1000` with default flags and `finalized 0 of 1000` with `--finalization=disabled`. The objects were still collected in the second run; only the finalizers were skipped. Running a test suite with that flag shows whether anything depends on them."
   },
   "refs": [
    {"title": "Cleaner source at jdk-25-ga: the rules for cleaning actions", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/Cleaner.java", "kind": "docs"},
    {"title": "JEP 421: Deprecate Finalization for Removal", "url": "https://openjdk.org/jeps/421", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Who holds a reference to the outer object",
  "java": {"title": "ThumbnailWriter.java", "src": "class ThumbnailWriter {\n    private final Path tempFile;\n\n    // inner (the default in Java): holds ThumbnailWriter.this\n    class Cleanup implements Runnable {\n        public void run() { deleteQuietly(tempFile); }\n    }\n\n    // static nested: holds only what you pass in\n    static class SafeCleanup implements Runnable {\n        private final Path file;\n        SafeCleanup(Path file) { this.file = file; }\n        public void run() { deleteQuietly(file); }\n    }\n}"},
  "kotlin": {"title": "ThumbnailWriter.kt", "src": "class ThumbnailWriter(private val tempFile: Path) {\n\n    // inner (you must ask for it in Kotlin): holds this@ThumbnailWriter\n    inner class Cleanup : Runnable {\n        override fun run() = deleteQuietly(tempFile)\n    }\n\n    // nested (the default in Kotlin): holds only what you pass in\n    class SafeCleanup(private val file: Path) : Runnable {\n        override fun run() = deleteQuietly(file)\n    }\n}"},
  "note": "The defaults are opposite. A class declared inside a class is inner in Java unless you write `static`, and nested in Kotlin unless you write `inner`. So a Java cleaning action written as a plain inner class silently holds the object it should clean, while the same code in Kotlin doesn't. Lambdas behave the same in both: one that reads a property or a field captures `this`. Kotlin also has no `override` for `finalize()`: to write one you declare `protected fun finalize()`, which is one more reason not to."
 },
 "worked": {
  "title": "Find why a WeakHashMap keeps growing",
  "steps": [
   {"say": "The service shows a progress bar for every upload. It keeps the progress in a `WeakHashMap` keyed by the upload, so finished uploads drop out by themselves once nothing else refers to them. Each entry also holds a callback that tells the photo's owner when the upload is done. The map grows all day and never shrinks. Read the code and look for a strong path back to the key.",
    "code": "record UploadProgress(AtomicLong bytesReceived, Runnable onDone) {}\n\nstatic final Map<Upload, UploadProgress> PROGRESS = new WeakHashMap<>();\n\nstatic void track(Upload upload) {\n    PROGRESS.put(upload, new UploadProgress(new AtomicLong(), () -> notifyOwner(upload.owner())));\n}",
    "lang": "java",
    "alt_code": "data class UploadProgress(val bytesReceived: AtomicLong, val onDone: () -> Unit)\n\nval PROGRESS: MutableMap<Upload, UploadProgress> = WeakHashMap()\n\nfun track(upload: Upload) {\n    PROGRESS[upload] = UploadProgress(AtomicLong()) { notifyOwner(upload.owner) }\n}",
    "alt_lang": "kotlin"},
   {"say": "1. Follow the references from a GC root. The static field holds the map, the map holds its entries, and each entry holds its value strongly. The value holds the callback, and the callback is a lambda that captured `upload`, because it calls `upload.owner()` later. So every finished upload is still strongly reachable from `PROGRESS`, through its own progress record, and its weak key is never cleared.",
    "code": "static PROGRESS -> WeakHashMap -> Entry (weak key, STRONG value)\n                                    -> UploadProgress -> onDone lambda -> upload   <- the key itself",
    "lang": "text"},
   {"say": "2. Break the strong path. The callback only needs the owner's name, so read it once, before building the lambda, and capture that instead of the upload.",
    "code": "static void track(Upload upload) {\n    String owner = upload.owner();                                       // capture the name, not the upload\n    PROGRESS.put(upload, new UploadProgress(new AtomicLong(), () -> notifyOwner(owner)));\n}",
    "lang": "java",
    "alt_code": "fun track(upload: Upload) {\n    val owner = upload.owner                                             // capture the name, not the upload\n    PROGRESS[upload] = UploadProgress(AtomicLong()) { notifyOwner(owner) }\n}",
    "alt_lang": "kotlin"},
   {"say": "3. Prove it with a test that doesn't trust timing. Drop the upload, keep a weak probe on it with its own queue, ask for GCs until the probe arrives (with a limit), then check the map. `size()` removes cleared entries before it counts.",
    "code": "Upload u = newTestUpload();\ntrack(u);\nReferenceQueue<Object> q = new ReferenceQueue<>();\nWeakReference<Object> probe = new WeakReference<>(u, q);\nu = null;\nReference<?> seen = null;\nfor (int i = 0; i < 50 && seen == null; i++) { System.gc(); seen = q.remove(50); }   // bounded wait\nassertThat(seen).isSameAs(probe);\nassertThat(PROGRESS).isEmpty();",
    "lang": "java",
    "alt_code": "var u: Upload? = newTestUpload()\ntrack(u!!)\nval q = ReferenceQueue<Any>()\nval probe = WeakReference<Any>(u, q)\nu = null\nvar seen: Reference<*>? = null\nfor (i in 0 until 50) { System.gc(); seen = q.remove(50); if (seen != null) break }   // bounded wait\nassertThat(seen).isSameAs(probe)\nassertThat(PROGRESS).isEmpty()",
    "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A Cleaner that runs, and a registry that forgets",
  "minutes": 14,
  "files": [
   "labs/memory/src/main/java/workbench/memory/l03/NativeBuffer.java",
   "labs/memory/src/main/java/workbench/memory/l03/WeakListenerRegistry.java",
   "labs/memory/src/main/java/workbench/memory/l03/NativeMemory.java"
  ],
  "run": "./gradlew :memory:test --tests 'workbench.memory.l03.*'",
  "steps": [
   "Run the tests. Four of seven fail, and the GC waits make the failing run take several seconds. `NativeMemory` stands in for a native library such as an image decoder: read it, but don't change it.",
   "Fix `NativeBuffer.close()`: keep the `Cleaner.Cleanable` that `register` returns, and call its `clean()`. A second close then does nothing.",
   "Find out why a forgotten buffer is never cleaned. Look hard at the lambda: what does `handle` mean inside it? Replace it with a `static` nested class or a `record` that holds only the `NativeMemory` and the handle value.",
   "Make `WeakListenerRegistry` hold `WeakReference<L>`. `size()` drops cleared references before counting. `fire()` drops them too, and holds a strong reference to each plugin while it calls it.",
   "Run the tests until all seven pass, then twice more."
  ],
  "hints": [
   "A field read inside a lambda is `this.field`, so the lambda captures `this`. Copying the field to a local variable first would also work, but a small static class makes the rule visible to the next reader.",
   "`list.removeIf(ref -> ref.get() == null)` drops the cleared references.",
   "The tests never assume a GC happened. They ask for one up to 50 times and wait on a `ReferenceQueue` or a condition, so a correct solution passes in well under a second.",
   "`Reference.reachabilityFence(plugin)` in a test keeps `plugin` strongly reachable until that line, even if the JIT sees no later use of the variable."
  ],
  "done_when": "All 7 tests in `ReachabilityTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write a Cleaner-backed temp file from memory",
  "minutes": 5,
  "prompt": "Close the page. Write a class `TempPreview` that creates a temp file in its constructor, deletes it in `close()`, and deletes it from a `Cleaner` if nobody closes it. `close()` must be safe to call twice. Check your cleaning action: what does it refer to?",
  "answer": {
   "lang": "java",
   "src": "final class TempPreview implements AutoCloseable {\n    private static final Cleaner CLEANER = Cleaner.create();\n    private final Path file;\n    private final Cleaner.Cleanable cleanable;\n\n    TempPreview() throws IOException {\n        file = Files.createTempFile(\"preview-\", \".jpg\");\n        cleanable = CLEANER.register(this, new Delete(file));   // Delete holds the path, not this\n    }\n\n    private record Delete(Path file) implements Runnable {\n        public void run() {\n            try { Files.deleteIfExists(file); } catch (IOException ignored) { }\n        }\n    }\n\n    Path file() { return file; }\n\n    @Override public void close() { cleanable.clean(); }        // at most once\n}",
   "alt": {
    "lang": "kotlin",
    "src": "class TempPreview : AutoCloseable {\n    val file: Path = Files.createTempFile(\"preview-\", \".jpg\")\n    private val cleanable = CLEANER.register(this, Delete(file))   // Delete holds the path, not this\n\n    private class Delete(private val file: Path) : Runnable {        // nested, not inner\n        override fun run() {\n            try { Files.deleteIfExists(file) } catch (ignored: IOException) { }\n        }\n    }\n\n    override fun close() = cleanable.clean()                          // at most once\n\n    companion object { private val CLEANER: Cleaner = Cleaner.create() }\n}"
   }
  }
 },
 "recap": [
  "The GC keeps what it can reach from the roots (thread stacks, static fields, native references) and frees the rest, at a time it chooses. Reference objects add looser rungs: soft, weak and phantom.",
  "Soft references are cleared before an `OutOfMemoryError` and at no promised time otherwise. They empty in bulk under pressure, so they make poor service caches.",
  "Weak references are cleared by the next GC that finds their object. Use them to attach data to objects you don't own (`WeakHashMap`, listener registries), never for caches. A value that refers to its own key keeps the entry forever.",
  "`Cleaner` replaces `finalize()`, which is deprecated for removal. The cleaning action must not refer to the object it cleans, and `close()` should call `cleanable.clean()`.",
  "`System.gc()` is a request. Use it in demos and in bounded test helpers that wait on a `ReferenceQueue`, never in service code.",
  "The limit: references and `Cleaner` tell you when the GC has decided. They can't make it decide sooner, so anything that must be released on time needs an explicit `close()`."
 ],
 "closing": """We started with a cleaning crew that follows the notes from the desks and the noticeboard, and keeps whatever it reaches. The GC works from its roots the same way, and Java adds three looser notes: soft for "keep it if there's room", weak for "keep it while someone else holds it", and phantom for "tell me after it's gone".

Now search your own code for `SoftReference`, `WeakHashMap` and `finalize`. For each one, ask what really holds the object, and when it would be released.

Next, we'll watch the crew itself at work. How does a collector find the live boxes in a big heap without stopping the program for long, and why does G1 split the floor into regions?""",
 "quiz": [
  {
   "q": "A `WeakHashMap<Album, AlbumView>` keeps growing even after albums are deleted everywhere else. `AlbumView` has a field `Album album` used for logging. What is the cause?",
   "options": [
    "`WeakHashMap` only removes entries after `System.gc()`",
    "Each value strongly refers to its own key, so the keys never become weakly reachable",
    "`Album` doesn't override `equals` and `hashCode`",
    "The map needs a `ReferenceQueue` to remove entries"
   ],
   "answer": 1,
   "why": "Values in a `WeakHashMap` are strong. A value that points back to its key gives the key a strong path from the map itself, so the GC never clears it. Normal GCs clear weak keys without any `System.gc()`, and the map already manages its own internal queue: `size()`, `get()` and `put()` remove stale entries."
  },
  {
   "q": "You need a cache of watermark pictures that the service reloads from disk on a miss. Which choice fits best?",
   "options": [
    "`Map<String, WeakReference<Picture>>`",
    "`Map<String, SoftReference<Picture>>`",
    "A cache with a maximum size and an expiry time, and a heap sized for it",
    "`Map<String, PhantomReference<Picture>>`"
   ],
   "answer": 2,
   "why": "A bounded cache keeps exactly as much as you decided, and expiry keeps its contents fresh. Weak values are gone at the next GC, so the hit rate collapses. Soft values stay until the heap is nearly full and then go in bulk during full GCs, sending all the reloads at once. A phantom reference can't even return its value."
  },
  {
   "q": "A class registers `CLEANER.register(this, () -> codec.release(nativeHandle))`, where `codec` and `nativeHandle` are fields. One code path forgets to call `close()`. What happens to the native memory?",
   "options": [
    "The cleaner frees it at the next GC",
    "The cleaner frees it when the JVM exits",
    "It is never freed, because the lambda captures `this` and the object never becomes phantom reachable",
    "The JVM throws an exception when the object is collected"
   ],
   "answer": 2,
   "why": "Reading `codec` and `nativeHandle` inside the lambda means `this.codec` and `this.nativeHandle`, so the lambda holds `this`. The cleaner holds the lambda, so the object stays strongly reachable forever: a leak of both the object and its native memory. The Javadoc also makes no promise that cleaners run at exit."
  },
  {
   "q": "A library you use still overrides `finalize()`. What's the cheapest way to find out whether your program relies on it before finalization is removed?",
   "options": [
    "Run the program and its tests with `--finalization=disabled`",
    "Run with `-XX:+DisableExplicitGC`",
    "Search the logs for `Finalizer`",
    "Call `System.runFinalization()` after each request"
   ],
   "answer": 0,
   "why": "`--finalization=disabled` (JDK 18 and later) stops every finalizer from running, which is exactly the world after removal. If the tests and a load run pass, nothing depends on it. `DisableExplicitGC` only ignores `System.gc()`, and calling `runFinalization` makes the dependency worse."
  },
  {
   "q": "From the threads track: a task on a fixed pool of one thread does `buffer.set(new byte[1 << 20])` on a `ThreadLocal` and never calls `remove()`. The task finishes. When can that 1 MiB array be collected?",
   "options": [
    "At the next GC, because the task is done",
    "Only when a later task on that same pool thread calls `buffer.remove()`, or the thread ends",
    "When the `ThreadLocal` object itself is garbage collected",
    "Never, while the JVM runs"
   ],
   "answer": 1,
   "why": "The value lives in the pool thread's own map, and a live thread is a GC root. In the research behind this course, a weak probe on the array stayed set after five `System.gc()` calls and cleared only after a task called `remove()` on the same pooled thread. The thread outlives every task, so the value does too.",
   "from": "conc-11"
  }
 ],
 "flashcards": [
  {"front": "What are GC roots?", "back": "Where reachability starts: local variables on live threads' stacks, static fields, and references held by native code."},
  {"front": "When is a `SoftReference` guaranteed to be cleared?", "back": "Before the JVM throws an `OutOfMemoryError`. At any other time, the specification promises nothing."},
  {"front": "When is a `WeakReference` cleared?", "back": "By the next GC that finds its object reachable only through weak references."},
  {"front": "What does `PhantomReference.get()` return?", "back": "Always `null`. A phantom reference only tells you, through its queue, that the object is gone."},
  {"front": "In a `WeakHashMap`, what keeps an entry alive forever?", "back": "A value that refers to its own key, directly or indirectly. Values are strong."},
  {"front": "Why might a `Cleaner` action never run?", "back": "The action refers to the object it cleans (a lambda reading a field, a Java inner class), so the object never becomes phantom reachable."},
  {"front": "How do you test whether code still relies on finalizers?", "back": "Run it with `--finalization=disabled` (JDK 18 and later): no finalizer runs."}
 ],
 "terms": [
  {"term": "GC root", "plain": "A starting point for reachability: a live thread's stack, a static field, a native reference."},
  {"term": "Strongly reachable", "plain": "Reachable through ordinary references. The GC never frees it."},
  {"term": "SoftReference", "plain": "A reference the GC clears when memory is short, at the latest before an OutOfMemoryError."},
  {"term": "WeakReference", "plain": "A reference the GC clears as soon as nothing stronger holds the object."},
  {"term": "PhantomReference", "plain": "A reference whose get() is always null; it reports that an object is gone."},
  {"term": "ReferenceQueue", "plain": "Where the GC puts reference objects after clearing them, so your code can react."},
  {"term": "Cleaner", "plain": "Runs a cleanup action after an object becomes phantom reachable, or when you call clean()."},
  {"term": "Finalization", "plain": "The old finalize() mechanism. Deprecated for removal since JDK 18."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to free a native decoder handle in `finalize()` \"in case someone forgets to close it\". Explain what you would do instead, and the one rule that makes it work.",
  "answer": "`finalize()` is deprecated for removal, runs on one thread at no set time, and can even be switched off with `--finalization=disabled`. Make the class `AutoCloseable` and close it with try-with-resources, so the handle is released at a known point. As a safety net, register the object with a shared `Cleaner` and keep the `Cleanable`; `close()` calls `cleanable.clean()`, which runs the action at most once. The rule: the cleaning action must not refer to the object. Put the handle in a small static class or record, not in a lambda that reads a field, or the object can never become phantom reachable and the action never runs. If the cleaner ever fires, log it, because it means a code path forgot to close."
 },
 "deeper": {
  "minutes": 8,
  "body": "There's a race the `Cleaner` pattern can hit even when you follow the rule. The JVM may decide an object is unreachable earlier than the source suggests, even while one of its methods is still running. The `Reference.reachabilityFence` Javadoc describes it: the JIT can load a field's value early, the object is then no longer needed, and the cleaner's thread can free a resource that the method is about to use.\n\nSo a method that passes a native handle to native code should keep its object reachable until the call returns:\n\n```java\npublic int decode(byte[] input) {\n    try {\n        return Decoder.decode(handle, input);      // native call that uses the handle\n    } finally {\n        Reference.reachabilityFence(this);         // `this` stays reachable until here\n    }\n}\n```\n\n```kotlin\nfun decode(input: ByteArray): Int {\n    try {\n        return Decoder.decode(handle, input)       // native call that uses the handle\n    } finally {\n        Reference.reachabilityFence(this)          // `this` stays reachable until here\n    }\n}\n```\n\nThe lab's tests use the same method for the opposite reason: to keep a plugin strongly reachable until the asserts are done. Its Javadoc also states a guarantee in the terms of the memory model track: actions in a thread before `reachabilityFence(x)` happen-before the garbage collector clears any reference to `x`, so a cleanup thread sees everything the method wrote.\n\nTwo more details are useful. Phantom references used to keep their object in memory until you cleared them; since JDK 9 the GC clears them automatically when it enqueues them, which is why `Cleaner` works without extra steps. And a `Cleaner` owns a daemon thread, so create one per library (a `static final` field), never one per object."
 },
 "sources": [
  {"title": "java.lang.ref package docs at jdk-25-ga: reachability", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/package-info.java"},
  {"title": "Cleaner source at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/Cleaner.java"},
  {"title": "WeakHashMap source at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/WeakHashMap.java"},
  {"title": "JEP 421: Deprecate Finalization for Removal", "url": "https://openjdk.org/jeps/421"}
 ]
}

(ROOT / "content/lessons/mem-03.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-03")
