import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l08"
K = "kotlin/workbench/nio/l08"
read = lambda p: (ROOT / p).read_text()

def box(x, y, w, h, cls, lines):
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>']
    for i, line in enumerate(lines):
        c = "t-s" if i == 0 else "t-s t-m"
        out.append(f'<text class="{c}" x="{x + w // 2}" y="{y + 20 + i * 17}" text-anchor="middle">{line}</text>')
    return "".join(out)

FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="A virtual thread calls read. The JDK socket code gets EAGAIN, registers '
    'the socket with its poller and parks the virtual thread, freeing the carrier. A poller thread waits in epoll_wait and '
    'unparks the virtual thread when data arrives">'
    + box(20, 14, 240, 44, "box-a", ["virtual thread: in.read()", "your blocking code"])
    + '<line class="ln" x1="140" y1="58" x2="140" y2="82" marker-end="url(#arr)"/>'
    + box(20, 86, 240, 44, "box", ["NioSocketImpl: non-blocking read", "returns EAGAIN: nothing yet"])
    + '<line class="ln" x1="140" y1="130" x2="140" y2="154" marker-end="url(#arr)"/>'
    + box(20, 158, 240, 44, "box", ["Poller.poll(fd), then park", "the carrier runs other work"])
    + '<line class="ln-d" x1="260" y1="180" x2="326" y2="108" marker-end="url(#arr)"/>'
    + '<text class="t-s t-m" x="295" y="168" text-anchor="middle">fd,</text>'
    + '<text class="t-s t-m" x="295" y="184" text-anchor="middle">one-shot</text>'
    + box(330, 86, 330, 44, "box-b", ["poller thread: epoll_wait on all fds", "JDK 21: Read-Poller; JDK 22+ Linux: MasterPoller"])
    + '<line class="ln-a" x1="495" y1="130" x2="495" y2="154" marker-end="url(#arr)"/>'
    + box(330, 158, 330, 44, "box-ok", ["data arrives: unpark the virtual thread", "it remounts on a free carrier, read() returns"])
    + box(20, 236, 640, 44, "box-dim", ["carrier threads: ForkJoinPool workers, one per core",
                                        "they run other virtual threads while this one waits"])
    + '</svg>'
)

export_kotlin = """private val exportSlots = Semaphore(maxConcurrentExports)   // the database allows 4

fun export(day: String, out: SocketChannel) {
    exportSlots.acquire()                                 // waiting here parks the virtual thread
    try {
        Thread.sleep(QUERY_MILLIS)                        // the statement query
        FileChannel.open(statements.resolve("$day.csv")).use { file ->
            FileSender.transferFully(file, 0, file.size(), out)   // sendfile on Linux
        }
    } finally {
        exportSlots.release()
    }
}"""
export_java = """private final Semaphore exportSlots = new Semaphore(maxConcurrentExports);   // the database allows 4

void export(String day, SocketChannel out) throws Exception {
    exportSlots.acquire();                                // waiting here parks the virtual thread
    try {
        Thread.sleep(QUERY_MILLIS);                       // the statement query
        try (FileChannel file = FileChannel.open(statements.resolve(day + ".csv"))) {
            FileSender.transferFully(file, 0, file.size(), out);   // sendfile on Linux
        }
    } finally {
        exportSlots.release();
    }
}"""
transfer_kotlin = """fun transferFully(file: FileChannel, position: Long, count: Long, target: WritableByteChannel): Int {
    var sent = 0L
    var calls = 0
    while (sent < count) {
        sent += file.transferTo(position + sent, count - sent, target)   // may be partial
        calls++
    }
    return calls
}"""
transfer_java = """static int transferFully(FileChannel file, long position, long count, WritableByteChannel target) throws IOException {
    long sent = 0;
    int calls = 0;
    while (sent < count) {
        sent += file.transferTo(position + sent, count - sent, target);   // may be partial
        calls++;
    }
    return calls;
}"""

L = {
 "id": "io-08",
 "title": "Zero-copy, epoll, io_uring, and choosing a server model",
 "minutes": 38,
 "goal": "By the end you can send files with zero-copy and handle partial transfers, explain readiness (epoll) versus completion (io_uring), describe how a virtual thread's blocking read waits on the JDK's poller in JDK 21 and later, and choose a server model for a payments service.",
 "warmup": {
  "q": "2,000 virtual threads on JDK 21 are each blocked in `socket.getInputStream().read()`. Roughly how many platform threads does the JVM have?",
  "options": [
   "About 2,000: each blocked read still needs an OS thread underneath",
   "About 15: the carriers (one per core), a few JDK poller threads, and the JVM's own threads",
   "Exactly 4: the carriers do all the waiting",
   "About 1,000: the JDK pairs two virtual threads per OS thread"
  ],
  "answer": 1,
  "why": "A blocked virtual thread is parked, not running, and it holds no OS thread. The JDK registers each socket with an internal poller that waits in `epoll_wait`, so the only extra platform threads are the poller threads. This lesson's demo counted 14 platform threads for 2,000 blocked readers on JDK 21: 4 carriers, `Read-Poller`, `Write-Poller`, two updater threads and JVM housekeeping."
 },
 "sections": [
  {
   "h": "Zero-copy: let the kernel move the file",
   "body": """Sending a file the obvious way passes every byte through your process twice. `read` copies bytes from the kernel's page cache (its in-memory copy of recently used file pages) into your buffer, and `write` copies them back into the kernel's socket send buffer. With a heap `ByteBuffer`, the JDK adds another copy through a temporary direct buffer, as lesson 2 showed. Each call is also a system call: a switch from your program into the kernel and back.

`FileChannel.transferTo` asks the kernel to do the whole move. On Linux, with a socket as the target, the JDK uses `sendfile(2)`: the kernel sends pages from the page cache straight to the socket, and the bytes never enter your process. A run for this track sent 64 MiB to a loopback socket and counted system calls with `strace`:

```text
transferTo:                            sendfile 1 call
copy through a 64 KiB heap buffer:     read 2,119 calls, write 1,037 calls, no sendfile
                                       (the reads include the receiving side)
```

Like `write` on a non-blocking socket, `transferTo` may move fewer bytes than you asked for. It returns how many it moved, so it lives in a loop:

```java
long sent = 0;
while (sent < count) {
    sent += file.transferTo(position + sent, count - sent, socket);   // maybe partial
}
```

```kotlin
var sent = 0L
while (sent < count) {
    sent += file.transferTo(position + sent, count - sent, socket)   // maybe partial
}
```

Netty wraps the same idea in `DefaultFileRegion`: write one to a channel and the transport sends the file. The NIO transport calls `FileChannel.transferTo`, and the native epoll transport calls `sendfile` itself. When the socket buffer fills, `sendfile` fails with `EAGAIN` (\"try again later\"), and Netty waits for writability and resumes: lesson 2's partial-write logic again.

Zero-copy has one condition: the bytes must leave exactly as they sit in the file. If the JVM encrypts them with TLS or compresses them, that work happens in your process, so the bytes have to come up into user space anyway. Tomcat's connector docs show the trade-off: for static files over 48 KiB it uses sendfile and skips compression. In payments, that makes zero-copy a tool for bulk transfers over plain internal links, such as settlement files and statement exports, where TLS ends at a proxy in front of the JVM.""",
   "try": {
    "title": "Count the system calls",
    "minutes": 4,
    "steps": [
     "Run `ZeroCopyDemo` (or `ZeroCopyDemoKt`) with the command below. It sends a 64 MiB file twice: with `transferTo`, then through a 64 KiB heap buffer.",
     "Before looking at the times, predict how many `transferTo` calls the first pass makes.",
     "On Linux with `strace`, run it outside Gradle: `strace -f -c -e trace=sendfile,read,write java -cp nio/build/classes/java/demo workbench.nio.l08.ZeroCopyDemo`, and find the `sendfile` line."
    ],
    "code": {"lang": "java", "title": "ZeroCopyDemo.java", "src": read(f"{lab}/demo/{P}/ZeroCopyDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.ZeroCopyDemo",
             "file": f"{lab}/demo/{P}/ZeroCopyDemo.java",
             "alt": {"lang": "kotlin", "title": "ZeroCopyDemo.kt", "src": read(f"{lab}/demo/{K}/ZeroCopyDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.ZeroCopyDemoKt",
                     "file": f"{lab}/demo/{K}/ZeroCopyDemo.kt"}},
    "expect": "One `transferTo` call for all 64 MiB on loopback, against 1,024 read calls for the copy. The times are close and change from run to run (40 to 46 ms against 41 to 44 ms here), so a single run proves nothing about speed. `strace` shows the real difference: 1 `sendfile` call, against about a thousand `write` calls and twice as many `read` calls for the copying pass."
   }
  },
  {
   "h": "Readiness or completion: epoll and io_uring",
   "body": """Everything in this track so far uses readiness notification. `epoll` answers \"which sockets are ready?\", and then your loop makes the `read` or `write` system call itself: one call to wait, and one more per socket to move bytes.

io_uring is a newer Linux interface that works by completion instead. Your program and the kernel share two ring buffers in memory. You put requests on the submission ring, such as \"read up to 16 KiB from this socket into this buffer\", the kernel does the work, and it puts results on the completion ring: \"done, 4,096 bytes\". One system call can submit and collect many operations, and the kernel, not your thread, moves the bytes.

On the JVM you reach io_uring through Netty; the JDK's own selector and poller use `epoll`. Netty 4.2 moved io_uring out of the incubator into a first-class transport. Its package is `io.netty.channel.uring`, and you use it like the other transports: a `MultiThreadIoEventLoopGroup` with `IoUringIoHandler.newFactory()`, and the `IoUring` channel classes. Netty checks the kernel when it loads, and `IoUring.isAvailable()` says whether it can run on this machine.

Is it faster? Not reliably. This section's demo sends a 32 MiB `DefaultFileRegion` over every transport available:

```text
nio      received 33,554,432 bytes in 29 ms
epoll    received 33,554,432 bytes in 18 ms
kqueue   unavailable: java.lang.ExceptionInInitializerError
io_uring received 33,554,432 bytes in 65 ms
```

The research for this track saw the same order (86 ms for epoll, 159 ms for io_uring in one run). Under `strace`, io_uring made no `sendfile` calls at all; the work went through 2,061 `io_uring_enter` calls, and Netty's history shows that it splices a file region instead. The transport is also still changing: Netty 4.2.20 itself contains several io_uring fixes. So measure your own workload before you switch. The switch is small, one factory and one channel class, which makes it cheap to try and cheap to undo.""",
   "try": {
    "title": "Every transport on your machine",
    "minutes": 3,
    "steps": [
     "Predict which transports your machine supports: Linux has epoll and maybe io_uring; macOS has kqueue.",
     "Run `TransportsDemo` (or `TransportsDemoKt`). Run it twice and compare the times between runs, not only between transports."
    ],
    "code": {"lang": "java", "title": "TransportsDemo.java", "src": read(f"{lab}/demo/{P}/TransportsDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.TransportsDemo",
             "file": f"{lab}/demo/{P}/TransportsDemo.java",
             "alt": {"lang": "kotlin", "title": "TransportsDemo.kt", "src": read(f"{lab}/demo/{K}/TransportsDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.TransportsDemoKt",
                     "file": f"{lab}/demo/{K}/TransportsDemo.kt"}},
    "expect": "Every available transport delivers exactly 33,554,432 bytes; the code differs only in the factory and the channel class. On Linux with a recent kernel you see nio, epoll and io_uring, and kqueue reports itself unavailable. On macOS you see nio and kqueue. In my two runs epoll was fastest (18 and 25 ms) and io_uring slowest (65 and 53 ms), but the numbers move between runs by as much as they differ between transports."
   },
   "refs": [
    {"title": "Netty 4.2 Migration Guide: io_uring graduated", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md", "kind": "read"}
   ]
  },
  {
   "h": "Under a virtual thread's blocking read: the JDK's own event loop",
   "body": """When a virtual thread calls `socket.getInputStream().read()` and no bytes have arrived, no OS thread blocks. The JDK's sources and a thread dump show what happens instead:

1. The JDK's socket implementation, `NioSocketImpl`, keeps the socket in non-blocking mode, so the read returns at once with `EAGAIN`: nothing yet.
2. It registers the socket's file descriptor with an internal `Poller`, which uses `epoll` with `EPOLLONESHOT` (report once, then disarm), and parks the virtual thread. Its carrier, the platform thread that was running it, moves on to other virtual threads.
3. A poller thread waits in `epoll_wait` on every registered socket. When data arrives, it unparks the virtual thread, which is mounted on a free carrier and tries the read again.

A jcmd thread dump of a parked reader shows that path: `NioSocketImpl.read`, then `NioSocketImpl.park`, `Poller.poll`, `LockSupport.park` and `VirtualThread.park`.

Which threads do the polling depends on the JDK version. On JDK 21 the pollers are platform threads named `Read-Poller` and `Write-Poller`, plus `Read-Updater` and `Write-Updater` on Linux. This section's demo, on JDK 21, with 2,000 virtual threads blocked in `read()`:

```text
2000 virtual threads blocked in read(); platform threads: 14
   4 x ForkJoinPool-N-worker-N
   1 x Read-Poller
   1 x Read-Updater
   1 x Write-Poller
   1 x Write-Updater
   ...
wrote 1 byte to each socket: all 2,000 readers woke and finished in 36 ms
```

From JDK 22, Linux defaults to a mode the JDK source calls `VTHREAD_POLLERS`: one platform `MasterPoller` thread plus sub-pollers that are themselves virtual threads, scheduled like any other, which the source says \"helps to integrate polling with virtual thread scheduling\". That is the default on Linux in JDK 25, the current LTS; macOS keeps platform poller threads. From JDK 24, `jcmd <pid> Thread.vthread_pollers` lists the pollers.

So virtual threads don't make event loops obsolete. They put one inside the JDK, so your code can stay blocking-style while an `epoll` loop does the waiting.""",
   "figure": {"svg": FIG, "caption": "A virtual thread's blocking read is a non-blocking read plus park and unpark, driven by an epoll loop inside the JDK."},
   "try": {
    "title": "Find the pollers",
    "minutes": 4,
    "steps": [
     "Run `PollerDemo` (or `PollerDemoKt`). Predict the number of platform threads before you look.",
     "Run it with `-Pargs=5000` and predict again: which names grow, if any?",
     "If you have JDK 25 installed, run the class with it directly: `java -cp nio/build/classes/java/demo workbench.nio.l08.PollerDemo 2000 30`, and while it holds, run `jcmd <pid> Thread.vthread_pollers` with the pid it prints. Which poller names appear?"
    ],
    "code": {"lang": "java", "title": "PollerDemo.java", "src": read(f"{lab}/demo/{P}/PollerDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.PollerDemo",
             "file": f"{lab}/demo/{P}/PollerDemo.java",
             "alt": {"lang": "kotlin", "title": "PollerDemo.kt", "src": read(f"{lab}/demo/{K}/PollerDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.PollerDemoKt",
                     "file": f"{lab}/demo/{K}/PollerDemo.kt"}},
    "expect": "On JDK 21, about 14 platform threads, the same with 5,000 readers: one carrier per core plus `Read-Poller`, `Write-Poller` and the two updaters. All readers wake within tens of milliseconds once data arrives. On JDK 25 on Linux, the platform list shows a `MasterPoller` instead of the read and write pollers and their updaters, because the sub-pollers are virtual threads and `getAllStackTraces` lists only platform threads; `Thread.vthread_pollers` shows them all. (The JDK 25 names come from the JDK source; this track ran its demos on JDK 21.)"
   },
   "refs": [
    {"title": "sun.nio.ch.Poller source (JDK 25)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java", "kind": "read"}
   ]
  },
  {
   "h": "Choosing a server model for a payments service",
   "body": """After eight lessons the choice comes down to two questions: where does the waiting happen, and what limits it?

| If the service... | Choose | Watch out for |
|---|---|---|
| uses JDBC, JTA and blocking SDKs, and is IO-bound | thread-per-request on virtual threads: Quarkus `@RunOnVirtualThread`, Jetty's virtual threads executor | a limit per downstream; pinning on JDK 21 to 23; CPU-heavy work |
| has the same blocking stack and moderate traffic | a bounded worker pool: Quarkus plain endpoints, Jetty's `QueuedThreadPool` | size it with Little's law; the pool caps concurrency |
| is async end to end (reactive SQL, async HTTP, streaming) | an event loop: Vert.x, Netty, Quarkus `Uni` endpoints | never block the loop; backpressure |
| holds many idle long-lived connections (terminals, WebSockets) | an event loop, or virtual threads if the per-connection work blocks | memory per connection; idle timeouts |
| sends large files unchanged | zero-copy: `transferTo`, Netty's `DefaultFileRegion` | no TLS or compression inside the JVM |

Two rules hold in every row. Concurrency needs a limit somewhere. An event loop limits it by never waiting, and a pool by its size. With virtual threads you have to add one, because 10,000 parked threads will make 10,000 calls to your card issuer the moment they wake. The lab for this lesson is exactly that bug. And the model doesn't change latency: a 120 ms issuer call takes 120 ms in every row.

My default for a new payments service on Quarkus is plain blocking endpoints, moving to `@RunOnVirtualThread` when the worker pool becomes the limit, with JDBC and issuer calls behind explicit limits. Event loops and `Uni` earn their extra complexity when the whole stack is non-blocking or connection counts are very large. Whatever you choose, measure it: Little's law for threads, the lag probe and blocked-thread warnings for loops, and `strace -c` when you want to know what the kernel is really doing.""",
   "try": {
    "title": "Choose for three services",
    "minutes": 4,
    "steps": [
     "A card-present gateway keeps 8,000 TCP connections from terminals; each sends one 200-byte message a minute and the work per message is a 3 ms in-memory check. Choose a model.",
     "A refund service: Quarkus, Oracle through JDBC with JTA, a blocking acquirer SDK at 400 ms, 150 requests a second at peak. Choose a model and say where the limits go.",
     "A nightly job sends 2 GB settlement files to an internal archive over plain TCP. Choose how to send them."
    ],
    "expect": "The gateway is almost all idle connections and tiny non-blocking work: an event loop (Netty or Vert.x) fits, with an idle timeout and framing as in lesson 4. The refund service needs 150 × 0.4 = 60 requests in flight: plain blocking endpoints on the worker pool work, or `@RunOnVirtualThread`; either way, put `@Blocking` on JTA endpoints that return `Uni`, cap the acquirer SDK with a semaphore, and size the JDBC pool on purpose. The settlement job is zero-copy territory: `FileChannel.transferTo` in a loop (or Netty's `DefaultFileRegion`), since nothing has to change the bytes on the way."
   }
  }
 ],
 "analogy": "A virtual thread's blocking read is a coat check. The virtual thread hands the poller a ticket (the socket's file descriptor) and leaves the counter, so the carrier, the clerk, can serve the next person in line. When the coat arrives (data on the socket), the poller calls the ticket number, and whichever clerk is free hands the coat back. Zero-copy is the opposite of a coat check: the parcel never comes to the counter at all, the warehouse ships it straight to the door. The analogy breaks at speed: a real coat check is slow, while parking and unparking a virtual thread is cheap, which is why 2,000 readers woke in 36 ms in this lesson's demo.",
 "in_your_world": "Statement exports, settlement files and reconciliation reports are where zero-copy pays off in payments, provided TLS ends at the proxy or gateway in front of the JVM. For APIs, the choice of model matters more than the transport: most payment services are blocking stacks (Oracle, JDBC, JTA, vendor SDKs), and on JDK 21 or newer they can serve high concurrency on virtual threads, as long as every downstream sits behind an explicit limit. If your fleet still runs JDK 21, upgrading to the current LTS, JDK 25, brings both `synchronized` without pinning (JEP 491, from JDK 24) and virtual-thread pollers on Linux. Treat io_uring as an experiment to measure, not a default.",
 "mistake": "The common mistake is moving a blocking service to virtual threads and deleting the thread-pool limit with nothing in its place. The old pool of 200 threads was quietly protecting the database and the card issuer. Virtual threads remove that cap, so the next burst sends thousands of concurrent queries to a 20-connection pool or an issuer that allows 100 calls, and latency or error rates explode downstream. Put a `Semaphore` (or the client's own concurrency limit) around each fragile dependency, with a timeout on acquiring it, when you introduce virtual threads.",
 "compare": {
  "title": "A bounded zero-copy export on virtual threads",
  "java": {"title": "StatementServer.export, Java", "src": export_java},
  "kotlin": {"title": "StatementServer.export, Kotlin", "src": export_kotlin},
  "note": "Both use `java.util.concurrent.Semaphore`, and on a virtual thread `acquire()` parks without holding a carrier. A Kotlin team might reach for `kotlinx.coroutines.sync.Semaphore` with `withPermit { }` instead. That one only works inside coroutines and suspends rather than parks, so it fits a coroutine-based server, not this thread-per-connection one. `FileChannel.transferTo` is the same JDK call from both languages; Kotlin's `use {}` plays the part of Java's try-with-resources for the file channel."
 },
 "worked": {
  "title": "Design a statement-download service",
  "steps": [
   {"say": "Requirements: at month end, 600 statement downloads a minute; each needs a 1.5 s database query and about 0.5 s to send its file. The database team allows 8 concurrent statement queries. Little's law first.",
    "code": "arrival rate     = 600 / 60 s           = 10 requests/s\ntime in system   = 1.5 s + 0.5 s        = 2 s\nin flight        = 10 x 2               = 20 requests\nqueries at once  = capped at 8          -> requests wait for a slot, not for a thread",
    "lang": "text"},
   {"say": "Use one virtual thread per connection, so waiting for the query, for a slot or for a slow client costs no OS thread. Put the database's limit in a semaphore with a timeout, so an overloaded database turns into a fast error.",
    "code": "private final Semaphore querySlots = new Semaphore(8);\n\nvoid export(String day, SocketChannel out) throws Exception {\n    if (!querySlots.tryAcquire(2, TimeUnit.SECONDS)) {   // 1. wait for a slot, but not forever\n        throw new IllegalStateException(\"statement service busy\");\n    }\n    try {\n        renderStatement(day);                              // 2. 1.5 s query, parks the virtual thread\n    } finally {\n        querySlots.release();                              // 3. free the slot before the slow send\n    }\n    sendFile(day, out);\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "private val querySlots = Semaphore(8)\n\nfun export(day: String, out: SocketChannel) {\n    if (!querySlots.tryAcquire(2, TimeUnit.SECONDS)) {    // 1. wait for a slot, but not forever\n        throw IllegalStateException(\"statement service busy\")\n    }\n    try {\n        renderStatement(day)                               // 2. 1.5 s query, parks the virtual thread\n    } finally {\n        querySlots.release()                               // 3. free the slot before the slow send\n    }\n    sendFile(day, out)\n}"},
   {"say": "Send the file with zero-copy, in a loop, because `transferTo` can stop early when the client's socket is full. Releasing the query slot before this step matters: a slow client should hold a cheap virtual thread, not one of the 8 database slots.",
    "code": transfer_java, "lang": "java", "alt_lang": "kotlin", "alt_code": transfer_kotlin},
   {"say": "Check the conditions before you promise zero-copy. If TLS terminates inside the JVM, the bytes must be encrypted in user space and `transferTo` gives you no zero-copy; send through a buffer and stop worrying about it. If an ingress proxy terminates TLS, the JVM's socket is plain and `sendfile` applies. Either way, the design's real limit is the 8 query slots, not the transfer method.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Export statements with zero-copy on virtual threads, within a limit",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/FileSender.kt", f"{lab}/main/{K}/StatementServer.kt"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l08.*'",
  "steps": [
   "Run the tests. Two of three fail. The idle-connection test already passes: read it, it shows 300 parked virtual threads costing almost no platform threads.",
   "Write `FileSender.transferFully`: call `file.transferTo` in a loop until `count` bytes are sent, and return the number of calls. The first test feeds it a channel that accepts only 4 KiB per write, so a single call is never enough.",
   "Run the tests. The download test now fails on concurrency: all 20 exports ran at once.",
   "Fix `StatementServer.export`: add a `java.util.concurrent.Semaphore` with `maxConcurrentExports` permits, `acquire()` before `measured { ... }` and `release()` in a `finally`. Run the tests until all three pass."
  ],
  "hints": [
   "`transferTo` returns the number of bytes it moved this time; add it to the bytes sent so far and start the next call at `position + sent`.",
   "Acquire the permit outside `measured { }`, so that threads waiting for a permit don't count as running exports.",
   "Waiting in `Semaphore.acquire()` parks a virtual thread just like a socket read does: twenty waiting exports cost twenty parked virtual threads, not twenty OS threads."
  ],
  "done_when": "All three tests in `StatementServerTest` pass."
 },
 "drill": {
  "title": "Write the transfer loop from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `transferFully(file, position, count, target)` that sends `count` bytes of a `FileChannel` with `transferTo`, survives partial transfers and returns the number of calls. When does Linux turn it into `sendfile`, and when can't it be zero-copy?",
  "answer": {"lang": "kotlin", "src": transfer_kotlin + "\n// sendfile: when the target is a socket on Linux.\n// Not zero-copy when the bytes must be changed in the JVM first: TLS in the JVM, compression.",
             "alt": {"lang": "java", "src": transfer_java + "\n// sendfile: when the target is a socket on Linux.\n// Not zero-copy when the bytes must be changed in the JVM first: TLS in the JVM, compression."}}
 },
 "recap": [
  "Copying a file to a socket passes each byte through your process; `FileChannel.transferTo` becomes `sendfile(2)` on Linux and keeps the bytes in the kernel. It can stop early, so call it in a loop.",
  "Netty's `DefaultFileRegion` does zero-copy per transport. Zero-copy needs the bytes unchanged: TLS or compression inside the JVM rules it out.",
  "`epoll` reports readiness and you make the IO call; io_uring takes requests on a shared ring and reports completions. Netty 4.2 supports io_uring as a first-class transport, and in this track's runs it was not faster.",
  "A virtual thread's blocking socket read is a non-blocking read, a registration with the JDK's poller (`EPOLLONESHOT`) and a park. JDK 21 uses platform `Read-Poller` threads; JDK 22+ on Linux uses a `MasterPoller` plus virtual sub-pollers.",
  "Pick the model by where waiting happens: virtual threads or a worker pool for blocking stacks, event loops for async stacks and huge idle connection counts, zero-copy for unchanged files.",
  "Every model needs a concurrency limit somewhere; with virtual threads you add it yourself."
 ],
 "quiz": [
  {"q": "A service sends 200 MB settlement files to a partner over HTTPS, with TLS handled by the JVM. Does `FileChannel.transferTo` give zero-copy here?",
   "options": ["No: the JVM encrypts the bytes in user space, so they must pass through your process", "Yes: on Linux transferTo always becomes sendfile", "Only with the io_uring transport", "Only if the file is read into a direct ByteBuffer first"],
   "answer": 0,
   "why": "`sendfile` moves bytes from the page cache to the socket unchanged. TLS has to encrypt them first, and the JDK does that in your process, so the bytes come up into user space no matter which API you call. Zero-copy fits when TLS ends at a proxy in front of the JVM."},
  {"q": "`file.transferTo(0, size, socket)` returns a number smaller than `size`. What does that mean?",
   "options": ["An error occurred, and the socket should be closed", "The file is shorter than expected", "It moved only part of the data, for example because the socket buffer was full; call it again from the new position", "The kernel doesn't support sendfile"],
   "answer": 2,
   "why": "Like a non-blocking `write`, `transferTo` moves what it can and reports how much. A single call is not a guarantee. Loop until the count is sent, as the lab's `transferFully` does."},
  {"q": "On JDK 21, 5,000 virtual threads are blocked in socket reads. Which threads wait in `epoll_wait` on their behalf?",
   "options": ["5,000 platform threads, one per socket", "The ForkJoinPool carrier threads", "None: the kernel wakes virtual threads directly", "The JDK's poller threads (`Read-Poller` on JDK 21)"],
   "answer": 3,
   "why": "The JDK registers each socket with its `Poller`, and the poller thread waits in `epoll_wait` for all of them. Carriers only run virtual threads that are ready, and the kernel knows nothing about virtual threads."},
  {"q": "From the virtual threads track: 10,000 requests run on virtual threads, and each calls a card issuer that accepts 100 concurrent calls. What protects the issuer?",
   "options": ["Nothing: virtual threads are cheap", "A `Semaphore(100)` around the issuer call", "A fixed pool of 100 virtual threads", "Setting `jdk.virtualThreadScheduler.parallelism` to 100"],
   "answer": 1,
   "why": "Virtual threads should not be pooled, and the scheduler's parallelism controls carriers, not how many virtual threads call the issuer. A semaphore around the call is the limit; the other 9,900 virtual threads park cheaply while they wait.",
   "from": "vt-03"},
  {"q": "A Quarkus payments API uses Oracle through JDBC and a blocking acquirer SDK, at 300 requests a second and 150 ms each. Which model fits best?",
   "options": ["Reactive `Uni` endpoints on the IO thread", "Plain blocking endpoints on the worker pool, or `@RunOnVirtualThread`, with explicit limits on JDBC and the acquirer", "The io_uring transport, because it is faster", "A Netty server with blocking handlers on the event loop"],
   "answer": 1,
   "why": "The stack blocks, so it must not run on an event loop, which rules out `Uni` endpoints and blocking Netty handlers. Little's law gives 45 requests in flight, easy for a worker pool or virtual threads. The transport doesn't change the threading model."}
 ],
 "flashcards": [
  {"front": "What does `FileChannel.transferTo` to a socket become on Linux?", "back": "`sendfile(2)`: the kernel sends pages from the page cache to the socket; the bytes never enter your process."},
  {"front": "When can't you use zero-copy for a file transfer?", "back": "When the bytes must change on the way inside the JVM: TLS encryption done by the JVM, or compression."},
  {"front": "`transferTo` returned fewer bytes than you asked for. What next?", "back": "Call it again from `position + sent` with the remaining count, in a loop, until everything is sent."},
  {"front": "epoll vs io_uring in one line each?", "back": "epoll: tells you which sockets are ready, then you make the IO call (readiness). io_uring: you submit the IO on a shared ring and collect completions (completion)."},
  {"front": "What happens when a virtual thread's socket read finds no data?", "back": "`NioSocketImpl` gets `EAGAIN`, registers the fd with the JDK `Poller` (epoll, one-shot) and parks the virtual thread; a poller thread unparks it when data arrives."},
  {"front": "JDK 21 vs JDK 22+ (Linux) poller threads?", "back": "JDK 21: platform `Read-Poller`/`Write-Poller` (plus updater threads). JDK 22+: one platform `MasterPoller` plus virtual sub-pollers (`VTHREAD_POLLERS`)."},
  {"front": "With virtual threads, where must the concurrency limit come from?", "back": "From you: a semaphore or the client's own pool around each downstream. Virtual threads themselves limit nothing."}
 ],
 "terms": [
  {"term": "Page cache", "plain": "The kernel's in-memory copy of file pages that were read or written recently."},
  {"term": "System call", "plain": "A switch from your program into the kernel to ask for a service, such as read, write or sendfile."},
  {"term": "Zero-copy", "plain": "Moving data from a file to a socket without copying it through your process's memory."},
  {"term": "sendfile", "plain": "The Linux system call that sends file data to a socket inside the kernel."},
  {"term": "io_uring", "plain": "A Linux interface where programs submit IO requests on a shared ring and collect completions."},
  {"term": "Poller", "plain": "The JDK's internal epoll or kqueue loop that wakes virtual threads when their sockets are ready."},
  {"term": "EPOLLONESHOT", "plain": "An epoll flag: report the socket once, then stop until it is registered again."}
 ],
 "explain_back": {
  "prompt": "A teammate says \"we moved to virtual threads, so we don't need event loops anymore\". Explain what happens inside the JDK when a virtual thread blocks on a socket read, and what still needs your attention.",
  "answer": "When a virtual thread reads from a socket that has no data, the JDK's socket code does a non-blocking read, gets EAGAIN, registers the socket's file descriptor with an internal poller and parks the virtual thread. The carrier thread is free to run other virtual threads. A poller thread waits in epoll_wait on all registered sockets and unparks the virtual thread when data arrives. So there still is an event loop: it moved inside the JDK, which lets our code stay blocking-style. On JDK 21 the pollers are platform threads; from JDK 22 on Linux they are mostly virtual threads themselves. What still needs attention: virtual threads don't limit concurrency, so each downstream needs a semaphore or pool limit; pinning (synchronized before JDK 24, native code) and CPU-heavy work can hold carriers; and the requests still arrive on Netty event loops in Quarkus, which must never block."
 },
 "deeper": {
  "minutes": 10,
  "body": """Dan Kegel's C10K page, from lesson 1, compared ways to serve many clients. This track has now met each family on the JVM: readiness notification with a level-triggered `Selector` (lesson 2) and Netty's native epoll transport (lessons 3 and 4); completion-based IO with io_uring (this lesson); and one thread per client with blocking IO, which virtual threads made cheap again by running a readiness loop underneath.

The JDK's poller has knobs, though you should rarely need them. On JDK 21, `-Djdk.readPollers` sets the number of read pollers (a power of 2, default 1); with 4, a thread dump shows four `Read-Poller` threads. From JDK 22, `-Djdk.pollerMode` selects the mode: `1` for `SYSTEM_THREADS` (platform pollers, the JDK 21 behavior) and `2` for `VTHREAD_POLLERS`. The JDK source after the current LTS adds a third mode, `POLLER_PER_CARRIER` (`3`), in JDK 27, while the Linux default stays `VTHREAD_POLLERS`. In `VTHREAD_POLLERS` mode on Linux, the number of read pollers defaults to the highest power of 2 not above the CPU count, capped at 32.

Two smaller facts complete the picture. The JDK's `Selector` registers sockets level-triggered, while the poller uses one-shot registration: a selector serves the same socket again and again, while the poller wakes exactly one parked thread exactly once. And file IO is different from socket IO: a virtual thread reading a file does not go through the poller. As the virtual threads track explained, file operations capture the carrier while they run, which is one more reason zero-copy file sending is worth knowing about.

To check any of this on your own JDK, `jcmd <pid> Thread.dump_to_file -format=json dump.json` shows virtual threads and their stacks, and from JDK 24 `jcmd <pid> Thread.vthread_pollers` shows the pollers."""
 },
 "sources": [
  {"title": "sun.nio.ch.Poller source (JDK 25)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java"},
  {"title": "Linux DefaultPollerProvider source (JDK 25)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java"},
  {"title": "NioSocketImpl source (JDK)", "url": "https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/NioSocketImpl.java"},
  {"title": "Netty 4.2 Migration Guide (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md"},
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"}
 ]
}

out = ROOT / "content/lessons/io-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
