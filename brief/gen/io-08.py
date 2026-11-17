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
    'the socket with its poller and parks the virtual thread, freeing the carrier. A poller thread, the JDK\'s own light-watcher, waits in epoll_wait and '
    'unparks the virtual thread when data arrives">'
    + box(20, 14, 240, 44, "box-a", ["virtual thread: in.read()", "your blocking code"])
    + '<line class="ln" x1="140" y1="58" x2="140" y2="82" marker-end="url(#arr)"/>'
    + box(20, 86, 240, 44, "box", ["NioSocketImpl: non-blocking read", "returns EAGAIN: nothing yet"])
    + '<line class="ln" x1="140" y1="130" x2="140" y2="154" marker-end="url(#arr)"/>'
    + box(20, 158, 240, 44, "box", ["Poller.poll(fd), then park", "the carrier runs other work"])
    + '<line class="ln-d" x1="260" y1="180" x2="326" y2="108" marker-end="url(#arr)"/>'
    + '<text class="t-s t-m" x="295" y="168" text-anchor="middle">fd,</text>'
    + '<text class="t-s t-m" x="295" y="184" text-anchor="middle">one-shot</text>'
    + box(330, 86, 330, 44, "box-b", ["poller: the JDK's light-watcher, in epoll_wait", "JDK 21: Read-Poller; JDK 22+ Linux: MasterPoller"])
    + '<line class="ln-a" x1="495" y1="130" x2="495" y2="154" marker-end="url(#arr)"/>'
    + box(330, 158, 330, 44, "box-ok", ["data arrives: unpark the virtual thread", "it remounts on a free carrier, read() returns"])
    + box(20, 236, 640, 44, "box-dim", ["carrier threads: ForkJoinPool workers, one per core",
                                        "they run other virtual threads while this one waits"])
    + '</svg>'
)

export_kotlin = """private val exportSlots = Semaphore(maxConcurrentExports)   // the records database allows 4

fun export(day: String, out: SocketChannel) {
    exportSlots.acquire()                                 // waiting here parks the virtual thread
    try {
        Thread.sleep(QUERY_MILLIS)                        // the records query
        FileChannel.open(logbooks.resolve("$day.csv")).use { file ->
            FileSender.transferFully(file, 0, file.size(), out)   // sendfile on Linux
        }
    } finally {
        exportSlots.release()
    }
}"""
export_java = """private final Semaphore exportSlots = new Semaphore(maxConcurrentExports);   // the records database allows 4

void export(String day, SocketChannel out) throws Exception {
    exportSlots.acquire();                                // waiting here parks the virtual thread
    try {
        Thread.sleep(QUERY_MILLIS);                       // the records query
        try (FileChannel file = FileChannel.open(logbooks.resolve(day + ".csv"))) {
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

# ---------------------------------------------------------------- opening
OPENING = """Picture the loading dock behind our post office. A van arrives for a sack of parcels that is already packed and labeled. Nobody carries that sack to the counter, unpacks it, repacks it and carries it back. The dock hands it straight to the van. Yet that's exactly what a program does when it sends a file by reading it into a buffer and writing the buffer to a socket.

This last lesson of the track goes under every server we've met, down to the kernel, the core of the operating system. The kernel can hand a file to the network without your program touching a byte. It can report which boxes are lit, or take a whole list of jobs and report back later. And the JDK runs a light-watcher of its own for virtual threads.

The easy trap is to assume the newest tool is the fastest. Jetty 12: acceptors, selectors and thread pools left us at the selector. In this lesson, we'll skip the counter, compare two kinds of light board, watch the JDK's light-watcher work, and then choose a server model. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Sending a file over a **socket**, a program's end of a network connection, the obvious way passes every byte through your process, the running program, twice. `read` copies bytes from the kernel's **page cache**, its in-memory copy of recently used file pages, into your buffer. `write` copies them back into the kernel's send buffer for the socket. With a heap `ByteBuffer`, the JDK adds another copy through a temporary direct buffer, as lesson 2 showed. Each call is also a **system call**: a switch from your program into the kernel and back, which costs time of its own.

In the post office, that's the sack carried to the counter, unpacked and repacked. `FileChannel.transferTo` asks the kernel to do the whole move instead, from the dock to the van. On Linux, with a socket as the target, the JDK uses `sendfile(2)`: the kernel sends pages from the page cache straight to the socket, and the bytes never enter your process. That's **zero-copy**: no copy through your program's memory.

`ZeroCopyDemo` sends a 64 MiB file to a loopback socket, a connection from the machine to itself, twice, first with `transferTo` and then through a 64 KiB heap buffer. A run for this track counted the system calls with `strace`, a Linux tool that lists every system call a program makes:

```text
transferTo:                            sendfile 1 call
copy through a 64 KiB heap buffer:     read 2,119 calls, write 1,037 calls, no sendfile
                                       (the reads include the receiving side)
```

One call, against about three thousand. The times, though, were close: 78 ms against 74 ms in one run on a busy 4-core machine, and 56 against 38 ms in the next. With the file already in the page cache and a loopback socket, copying 64 MiB is quick, so one timing proves nothing either way. The system calls are the honest measure here: they count the work that zero-copy removes.

Like `write` on a non-blocking socket, `transferTo` may move fewer bytes than you asked for. It returns how many it moved, so it belongs in a loop:

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

Netty wraps the same idea in `DefaultFileRegion`: write one to a channel, and the transport sends the file. The NIO transport calls `FileChannel.transferTo`, and Netty's native epoll transport calls `sendfile` itself. When the socket's buffer fills, `sendfile` fails with `EAGAIN` ("try again later"), and Netty waits until the channel is writable and resumes: lesson 2's partial-write logic again.

Zero-copy has one condition: the bytes must leave exactly as they sit in the file. Suppose the JVM encrypts them with TLS, the encryption behind https, or compresses them. That work happens in your process, so the bytes have to come up into your memory anyway. The dock picture holds here too: a sack that must be opened on the way can't go straight to the van. Tomcat's connector docs show the trade-off: for static files over 48 KiB it uses sendfile and skips compression. So zero-copy is a tool for bulk files over plain links, or where TLS ends at a proxy in front of the JVM.

**When bytes leave exactly as they're stored, let the kernel move them. Call `transferTo` in a loop.**

Zero-copy saves the copies. The next question is how a server learns which sockets are ready at all."""

# ---------------------------------------------------------------- section 1
S1 = """Everything in this track so far uses **readiness** notification. `epoll`, the Linux mechanism behind our wall of lights, keeps the list of lit boxes for you. You register each socket once, and `epoll_wait` returns only the ones that are ready, so asking costs about the same with ten boxes or ten thousand. Then your loop makes the `read` or `write` system call itself: one call to wait, and one more per socket to move the bytes. The JDK registers sockets with `epoll` in level-triggered mode, so a light stays on while there's mail, as lesson 2 showed.

**io_uring** is a newer Linux interface that works by **completion** instead. Your program and the kernel share two ring buffers in memory, fixed-size queues whose ends wrap around to their starts, like a drop box with two trays. You put requests in the submission ring, such as "read up to 16 KiB from this socket into this buffer". The kernel does the work and puts the results in the completion ring: "done, 4,096 bytes". One system call can submit and collect many operations, and the kernel, not your thread, moves the bytes. In the post office, you leave a whole list of jobs in the drop box and collect the results later, instead of standing at the board waiting for lights.

On the JVM you reach io_uring through Netty; the JDK's own selector and poller use `epoll`. Netty 4.2 moved io_uring out of its incubator into a full transport. Its package is `io.netty.channel.uring`, and you use it like the other transports: a `MultiThreadIoEventLoopGroup` with `IoUringIoHandler.newFactory()`, and the `IoUring` channel classes. Netty checks the kernel when it loads, and `IoUring.isAvailable()` says whether it can run on this machine.

So is the drop box faster? Not reliably. `TransportsDemo` sends a 32 MiB `DefaultFileRegion` over every transport this machine offers. One run on a busy 4-core machine printed:

```text
nio      received 33,554,432 bytes in 137 ms
epoll    received 33,554,432 bytes in 35 ms
kqueue   unavailable: java.lang.ExceptionInInitializerError
io_uring received 33,554,432 bytes in 59 ms
```

`kqueue` is the macOS and BSD cousin of `epoll`, so on Linux it reports itself unavailable. Every transport delivered every byte. Epoll beat io_uring in this run, in its Kotlin twin's (40 against 48 ms) and in the research runs for this track (86 against 159 ms), and the gaps moved from run to run.

Under `strace`, io_uring made no `sendfile` calls at all. The work went through 2,061 `io_uring_enter` calls, and Netty's history shows that it splices a file region instead. (`splice` is another kernel call that moves data without copying it into your process.) The transport is also still changing: Netty 4.2.20 itself contains several io_uring fixes.

So measure your own workload before you switch. The switch is small, one factory and one channel class, which makes it cheap to try and cheap to undo.

**A newer kernel interface is a question, not an answer. Measure it on your own workload before you switch.**

Netty lets you pick the light board. A virtual thread has no such choice: when it waits on a socket, the JDK watches the lights for it."""

# ---------------------------------------------------------------- section 2
S2 = """When a virtual thread calls `socket.getInputStream().read()` and no bytes have arrived, no operating system thread blocks. A virtual thread runs on a **carrier**, an ordinary platform thread it borrows. The JDK's sources and a thread dump, a snapshot of every thread's stack, show what happens instead:

1. The JDK's socket code, `NioSocketImpl`, keeps the socket in non-blocking mode, so the read returns at once with `EAGAIN`: nothing yet.
2. It registers the socket's **file descriptor**, the number the kernel uses to name an open socket or file, with an internal `Poller`. The poller uses `epoll` with `EPOLLONESHOT` (report once, then disarm), and the JDK parks the virtual thread, which puts it to sleep until something wakes it. Its carrier moves on to other virtual threads.
3. A poller thread waits in `epoll_wait` on every registered socket. When data arrives, it unparks (wakes) the virtual thread, which goes back onto a free carrier and tries the read again.

In the post office, the temporary helper leaves a ticket with the JDK's light-watcher and takes a seat. When the light comes on, the watcher calls the ticket, and whichever desk is free carries on with the helper's job. A thread dump of a parked reader on JDK 25 shows the path, newest frame first:

```text
java.base/java.lang.VirtualThread.park(VirtualThread.java:745)
...
java.base/java.util.concurrent.locks.LockSupport.park(LockSupport.java:367)
java.base/sun.nio.ch.Poller.poll(Poller.java:197)
...
java.base/sun.nio.ch.NioSocketImpl.park(NioSocketImpl.java:174)
...
java.base/sun.nio.ch.NioSocketImpl.implRead(NioSocketImpl.java:307)
...
workbench.nio.l08.PollerDemo.lambda$main$0(PollerDemo.java:33)
```

Which threads do the polling depends on the JDK version. `PollerDemo` blocks 2,000 virtual threads in `read()` and counts the platform threads. On JDK 21 it printed:

```text
2000 virtual threads blocked in read(); platform threads: 14
   4 x ForkJoinPool-N-worker-N
   1 x Read-Poller
   1 x Read-Updater
   1 x Write-Poller
   1 x Write-Updater
   ...
wrote 1 byte to each socket: all 2,000 readers woke and finished in 114 ms
```

The four `ForkJoinPool` workers are the carriers, one per core. The pollers are platform threads named `Read-Poller` and `Write-Poller`, with two updater threads beside them on Linux. Two thousand waiting readers cost no extra platform threads at all.

From JDK 22, Linux defaults to a mode the JDK source calls `VTHREAD_POLLERS`: one platform `MasterPoller` thread plus sub-pollers that are themselves virtual threads, scheduled like any other. The source says it \"helps to integrate polling with virtual thread scheduling\". The same demo on JDK 25, the current long-term support (LTS) release, printed 12 platform threads, with one `MasterPoller` and no read or write pollers among them. `jcmd <pid> Thread.vthread_pollers`, a command added in JDK 24, lists the rest:

```text
Master I/O poller:
sun.nio.ch.EPollPoller@50062f45 [registered = 5, owner = Thread[#547,MasterPoller,5,InnocuousThreadGroup]]

Read I/O pollers:
[0] sun.nio.ch.EPollPoller@3f48a9aa [registered = 599, owner = VirtualThread[#1505,SubPoller-0]/waiting]
[1] sun.nio.ch.EPollPoller@29c03991 [registered = 411, owner = VirtualThread[#1537,SubPoller-1]/waiting]
[2] sun.nio.ch.EPollPoller@309d6a91 [registered = 594, owner = VirtualThread[#1541,SubPoller-2]/waiting]
[3] sun.nio.ch.EPollPoller@4b9d1f8b [registered = 396, owner = VirtualThread[#1544,SubPoller-3]/waiting]
```

Four read sub-pollers on four cores, each a virtual thread, share the 2,000 sockets: 599, 411, 594 and 396. On macOS, the JDK keeps platform poller threads.

So virtual threads don't make event loops obsolete. They put one inside the JDK, so your code can stay blocking style while an `epoll` loop does the waiting.

**A virtual thread's blocking read is a non-blocking read, a ticket at the poller and a park. The event loop is still there, inside the JDK.**

We've now seen every way of waiting this track covers. The last job is to choose between them."""

# ---------------------------------------------------------------- section 3
S3 = """After eight lessons, choosing a server model comes down to two questions. Where does the waiting happen, and what limits it? A **downstream** is anything your service calls in turn, such as a database or another web service, and most waiting happens there:

| If the service... | Choose | Watch out for |
|---|---|---|
| calls its downstreams the blocking way and mostly waits | a thread per request on virtual threads: Quarkus `@RunOnVirtualThread`, Jetty's virtual threads executor | a limit per downstream; pinning on JDK 21 to 23; CPU-heavy work |
| has the same blocking code and moderate traffic | a bounded worker pool: Quarkus plain endpoints, Jetty's `QueuedThreadPool` | size it with Little's law; the pool caps concurrency |
| is non-blocking end to end (non-blocking database client, async HTTP, streaming) | an event loop: Vert.x, Netty, Quarkus `Uni` endpoints | never block the loop; backpressure |
| holds many idle connections that stay open for a long time | an event loop, or virtual threads if the work per connection blocks | memory per connection; idle timeouts |
| sends large files unchanged | zero-copy: `transferTo`, Netty's `DefaultFileRegion` | no TLS or compression inside the JVM |

Read the table with the post office in mind. The first two rows are clerks for customers who wait: temporary helpers, or a back office with a fixed staff. The third and fourth are one clerk per row of boxes, who never makes a phone call. The last is the loading dock.

Two rules hold in every row. First, concurrency needs a limit somewhere. An event loop limits it by never waiting, and a pool by its size. With virtual threads you have to add one, because 10,000 parked threads will make 10,000 calls to your database the moment they wake. This lesson's lab is exactly that bug.

Second, the model doesn't change latency. A 120 ms call to a slow web service takes 120 ms in every row. What changes is how many of those calls you can wait for at once, and what each wait costs you.

Here is where I'd start for a new web service that calls a database. Use plain blocking endpoints first. Move to virtual threads when the worker pool becomes the limit, with every database and outside call behind an explicit limit. Event loops and `Uni` earn their extra complexity when the whole stack is non-blocking, or when the connection counts are very large.

Whatever you choose, measure it. Use Little's law for threads, the lag probe and the blocked-thread warnings for loops, and `strace -c` when you want to know what the kernel is really doing.

**Choose the model by where your service waits. Then put a limit in front of everything it waits on.**"""

# ---------------------------------------------------------------- closing
CLOSING = """This track began with one clerk per customer and ends at the loading dock. On the way, the post office learned to watch a wall of lights, run a line of stations, use a back office, read labels, hire helpers, and let the kernel carry the sacks.

Now look in your own code for a loop that reads a file into a buffer and writes it to a socket, and for a virtual-thread service with nothing in front of its database.

Next, we'll start the Part 2 capstone and build a small quote service on Netty. What does a server look like when its event loop never waits for anything, and how can a test prove it?"""

L = {
 "id": "io-08",
 "title": "Zero-copy, epoll, io_uring, and choosing a server model",
 "minutes": 38,
 "goal": "By the end you can send files with zero-copy and handle partial transfers, explain readiness (epoll) versus completion (io_uring), describe how a virtual thread's blocking read waits on the JDK's poller in JDK 21 and JDK 25, and choose a server model from where a service waits.",
 "opening": OPENING,
 "warmup": {
  "q": "2,000 virtual threads on JDK 21 are each blocked in `socket.getInputStream().read()`. Roughly how many platform threads does the JVM have?",
  "options": [
   "About 2,000: each blocked read still needs an operating system thread underneath",
   "About 15: the carriers (one per core), a few JDK poller threads, and the JVM's own threads",
   "Exactly 4: the carriers do all the waiting",
   "About 1,000: the JDK pairs two virtual threads per operating system thread"
  ],
  "answer": 1,
  "why": "A blocked virtual thread is parked, not running, and it holds no operating system thread. The JDK registers each socket with an internal poller that waits in `epoll_wait`, so the only extra platform threads are the poller threads. This lesson's demo counted 14 platform threads for 2,000 blocked readers on JDK 21: 4 carriers, `Read-Poller`, `Write-Poller`, two updater threads and JVM housekeeping. On JDK 25 it counted 12."
 },
 "sections": [
  {
   "h": "Straight from the loading dock to the van: zero-copy with transferTo",
   "body": S0,
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
    "expect": "One `transferTo` call for all 64 MiB on loopback, against 1,024 read calls for the copy. The times are close and change from run to run (between 38 and 78 ms for either pass in this lesson's runs), so a single run proves nothing about speed. `strace` shows the real difference: 1 `sendfile` call, against about a thousand `write` calls and twice as many `read` calls for the copying pass."
   }
  },
  {
   "h": "A board of lit boxes, or a drop box for jobs: epoll and io_uring",
   "body": S1,
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
    "expect": "Every available transport delivers exactly 33,554,432 bytes; the code differs only in the factory and the channel class. On Linux with a recent kernel you see nio, epoll and io_uring, and kqueue reports itself unavailable. On macOS you see nio and kqueue. In this lesson's runs epoll was fastest every time (18 to 40 ms), io_uring took 48 to 65 ms, and nio anywhere from 29 to 137 ms: the numbers move between runs by as much as they differ between transports."
   },
   "refs": [
    {"title": "Netty 4.2 Migration Guide: io_uring graduated", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md", "kind": "read"}
   ]
  },
  {
   "h": "The JDK's own light-watcher: what a virtual thread's blocking read really does",
   "body": S2,
   "figure": {"svg": FIG, "caption": "A virtual thread's blocking read is a non-blocking read plus park and unpark, driven by an epoll loop inside the JDK."},
   "try": {
    "title": "Find the pollers",
    "minutes": 4,
    "steps": [
     "Run `PollerDemo` (or `PollerDemoKt`). Predict the number of platform threads before you look.",
     "Run it with `-Pargs=5000` and predict again: which names grow, if any?",
     "If you have JDK 25 installed, run the class with it directly: `java -cp nio/build/classes/java/demo workbench.nio.l08.PollerDemo 2000 30`, and while it holds, run `jcmd <pid> Thread.vthread_pollers` with the pid it prints. Which poller names appear, and how many read pollers?"
    ],
    "code": {"lang": "java", "title": "PollerDemo.java", "src": read(f"{lab}/demo/{P}/PollerDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.PollerDemo",
             "file": f"{lab}/demo/{P}/PollerDemo.java",
             "alt": {"lang": "kotlin", "title": "PollerDemo.kt", "src": read(f"{lab}/demo/{K}/PollerDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l08.PollerDemoKt",
                     "file": f"{lab}/demo/{K}/PollerDemo.kt"}},
    "expect": "On JDK 21, about 14 platform threads, the same with 5,000 readers: one carrier per core plus `Read-Poller`, `Write-Poller` and the two updaters. All readers wake within about a tenth of a second once data arrives. On JDK 25 on Linux, the platform list shows a `MasterPoller` instead of the read and write pollers and their updaters (12 platform threads in this lesson's run), because the sub-pollers are virtual threads and `getAllStackTraces` lists only platform threads. `Thread.vthread_pollers` shows them all: one read sub-poller per core up to 32, rounded down to a power of 2 (four on four cores), and one write sub-poller."
   },
   "refs": [
    {"title": "sun.nio.ch.Poller source (JDK 25)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java", "kind": "read"}
   ]
  },
  {
   "h": "Choosing a server model: where the waiting happens, and what limits it",
   "body": S3,
   "try": {
    "title": "Choose for three services",
    "minutes": 4,
    "steps": [
     "The 6,000 parcel lockers from lesson 1 keep TCP connections open all day; each sends one 200-byte message a minute, and the work per message is a 3 ms check in memory. Choose a model.",
     "A tracking service: Quarkus, a database it calls the blocking way with JTA transactions, a blocking library for a courier's web service at 400 ms, and 150 requests a second at peak. Choose a model and say where the limits go.",
     "A nightly job sends 2 GB logbook files to an archive over a plain internal link. Choose how to send them."
    ],
    "expect": "The lockers are almost all idle connections with tiny non-blocking work: an event loop (Netty or Vert.x) fits, with an idle timeout and framing as in lesson 4. The tracking service needs 150 x 0.4 = 60 requests in flight: plain blocking endpoints on the worker pool work, or `@RunOnVirtualThread`; either way, put `@Blocking` on JTA endpoints that return `Uni`, cap the courier library with a semaphore, and size the database pool on purpose. The nightly job is zero-copy territory: `FileChannel.transferTo` in a loop (or Netty's `DefaultFileRegion`), since nothing has to change the bytes on the way."
   }
  }
 ],
 "compare": {
  "title": "A bounded zero-copy export on virtual threads",
  "java": {"title": "LogbookServer.export, Java", "src": export_java},
  "kotlin": {"title": "LogbookServer.export, Kotlin", "src": export_kotlin},
  "note": "Both use `java.util.concurrent.Semaphore`, and on a virtual thread `acquire()` parks without holding a carrier. A Kotlin team might reach for `kotlinx.coroutines.sync.Semaphore` with `withPermit { }` instead. That one only works inside coroutines, and it suspends rather than parks, so it fits a coroutine-based server, not this server with a thread per connection. `FileChannel.transferTo` is the same JDK call from both languages; Kotlin's `use {}` plays the part of Java's try-with-resources for the file channel."
 },
 "worked": {
  "title": "Design a logbook-download service",
  "steps": [
   {"say": "Requirements: at month end, 600 logbook downloads a minute. Each needs a 1.5 s query to the records database and about 0.5 s to send its file. The database team allows 8 queries at once. Little's law first.",
    "code": "arrival rate     = 600 / 60 s           = 10 requests/s\ntime in system   = 1.5 s + 0.5 s        = 2 s\nin flight        = 10 x 2               = 20 requests\nqueries at once  = capped at 8          -> requests wait for a slot, not for a thread",
    "lang": "text"},
   {"say": "Use one virtual thread per connection, so waiting for the query, for a slot or for a slow client costs no operating system thread. Put the database's limit in a semaphore with a timeout, so an overloaded database turns into a fast error.",
    "code": "private final Semaphore querySlots = new Semaphore(8);\n\nvoid export(String day, SocketChannel out) throws Exception {\n    if (!querySlots.tryAcquire(2, TimeUnit.SECONDS)) {   // 1. wait for a slot, but not forever\n        throw new IllegalStateException(\"records database busy\");\n    }\n    try {\n        renderLogbook(day);                                // 2. 1.5 s query, parks the virtual thread\n    } finally {\n        querySlots.release();                              // 3. free the slot before the slow send\n    }\n    sendFile(day, out);\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "private val querySlots = Semaphore(8)\n\nfun export(day: String, out: SocketChannel) {\n    if (!querySlots.tryAcquire(2, TimeUnit.SECONDS)) {    // 1. wait for a slot, but not forever\n        throw IllegalStateException(\"records database busy\")\n    }\n    try {\n        renderLogbook(day)                                 // 2. 1.5 s query, parks the virtual thread\n    } finally {\n        querySlots.release()                               // 3. free the slot before the slow send\n    }\n    sendFile(day, out)\n}"},
   {"say": "Send the file with zero-copy, in a loop, because `transferTo` can stop early when the client's socket is full. Releasing the query slot before this step matters: a slow client should hold a cheap virtual thread, not one of the 8 database slots.",
    "code": transfer_java, "lang": "java", "alt_lang": "kotlin", "alt_code": transfer_kotlin},
   {"say": "Check the conditions before you promise zero-copy. If TLS ends inside the JVM, the bytes must be encrypted in your process, and `transferTo` gives you no zero-copy; send through a buffer and stop worrying about it. If a proxy in front of the JVM handles TLS, the JVM's socket is plain, and `sendfile` applies. Either way, the design's real limit is the 8 query slots, not the way the file is sent.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Send logbooks with zero-copy on virtual threads, within a limit",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/FileSender.kt", f"{lab}/main/{K}/LogbookServer.kt"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l08.*'",
  "steps": [
   "Run the tests. Two of three fail. `LogbookServer` sends a day's logbook file to each client, one virtual thread per connection. The idle-connection test already passes: read it, it shows 300 parked virtual threads costing almost no platform threads.",
   "Write `FileSender.transferFully`: call `file.transferTo` in a loop until `count` bytes are sent, and return the number of calls. The first test feeds it a channel that accepts only 4 KiB per write, so a single call is never enough.",
   "Run the tests. The download test now fails on concurrency: all 20 exports ran at once, against the records database's limit of 4.",
   "Fix `LogbookServer.export`: add a `java.util.concurrent.Semaphore` with `maxConcurrentExports` permits, `acquire()` before `measured { ... }` and `release()` in a `finally`. Run the tests until all three pass."
  ],
  "hints": [
   "`transferTo` returns the number of bytes it moved this time; add it to the bytes sent so far, and start the next call at `position + sent`.",
   "Acquire the permit outside `measured { }`, so that threads waiting for a permit don't count as running exports.",
   "Waiting in `Semaphore.acquire()` parks a virtual thread just as a socket read does: twenty waiting exports cost twenty parked virtual threads, not twenty operating system threads."
  ],
  "done_when": "All three tests in `LogbookServerTest` pass."
 },
 "drill": {
  "title": "Write the transfer loop from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `transferFully(file, position, count, target)` that sends `count` bytes of a `FileChannel` with `transferTo`, survives partial transfers and returns the number of calls. When does Linux turn it into `sendfile`, and when can't it be zero-copy?",
  "answer": {"lang": "kotlin", "src": transfer_kotlin + "\n// sendfile: when the target is a socket on Linux.\n// Not zero-copy when the JVM must change the bytes first: TLS in the JVM, compression.",
             "alt": {"lang": "java", "src": transfer_java + "\n// sendfile: when the target is a socket on Linux.\n// Not zero-copy when the JVM must change the bytes first: TLS in the JVM, compression."}}
 },
 "recap": [
  "Copying a file to a socket passes each byte through your process. `FileChannel.transferTo` becomes `sendfile(2)` on Linux and keeps the bytes in the kernel. It can stop early, so call it in a loop.",
  "Netty's `DefaultFileRegion` does zero-copy where the transport can. Zero-copy needs the bytes unchanged: TLS or compression inside the JVM rules it out.",
  "`epoll` reports readiness and you make the IO call; io_uring takes requests on a shared ring and reports completions. Netty 4.2 supports io_uring as a full transport, and in this track's runs it was not faster.",
  "A virtual thread's blocking socket read is a non-blocking read, a registration with the JDK's poller (`EPOLLONESHOT`) and a park. JDK 21 uses platform `Read-Poller` threads; JDK 22 and later on Linux use a `MasterPoller` plus virtual sub-pollers.",
  "Pick the model by where the waiting happens: virtual threads or a worker pool for blocking code, event loops for non-blocking code and huge numbers of idle connections, zero-copy for unchanged files.",
  "The limit: no model makes a slow call faster, and with virtual threads nothing limits concurrency unless you add the limit yourself."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A service sends 200 MB archive files to a partner over HTTPS, with TLS handled by the JVM. Does `FileChannel.transferTo` give zero-copy here?",
   "options": ["No: the JVM encrypts the bytes in your process, so they must pass through it", "Yes: on Linux transferTo always becomes sendfile", "Only with the io_uring transport", "Only if the file is read into a direct ByteBuffer first"],
   "answer": 0,
   "why": "`sendfile` moves bytes from the page cache to the socket unchanged. TLS has to encrypt them first, and the JDK does that in your process, so the bytes come up into your memory whichever API you call. Zero-copy fits when TLS ends at a proxy in front of the JVM."},
  {"q": "`file.transferTo(0, size, socket)` returns a number smaller than `size`. What does that mean?",
   "options": ["An error occurred, and the socket should be closed", "The file is shorter than expected", "It moved only part of the data, for example because the socket buffer was full; call it again from the new position", "The kernel doesn't support sendfile"],
   "answer": 2,
   "why": "Like a non-blocking `write`, `transferTo` moves what it can and reports how much. A single call is not a guarantee. Loop until the count is sent, as the lab's `transferFully` does."},
  {"q": "On JDK 21, 5,000 virtual threads are blocked in socket reads. Which threads wait in `epoll_wait` on their behalf?",
   "options": ["5,000 platform threads, one per socket", "The ForkJoinPool carrier threads", "None: the kernel wakes virtual threads directly", "The JDK's poller threads (`Read-Poller` on JDK 21)"],
   "answer": 3,
   "why": "The JDK registers each socket with its `Poller`, and the poller thread waits in `epoll_wait` for all of them. Carriers only run virtual threads that are ready, and the kernel knows nothing about virtual threads."},
  {"q": "From the virtual threads track: 10,000 requests run on virtual threads, and each calls an outside web service that accepts 100 calls at once. What protects that service?",
   "options": ["Nothing: virtual threads are cheap", "A `Semaphore(100)` around the call", "A fixed pool of 100 virtual threads", "Setting `jdk.virtualThreadScheduler.parallelism` to 100"],
   "answer": 1,
   "why": "Virtual threads should not be pooled, and the scheduler's parallelism controls carriers, not how many virtual threads make the call. A semaphore around the call is the limit; the other 9,900 virtual threads park cheaply while they wait.",
   "from": "vt-03"},
  {"q": "A Quarkus web service calls its database the blocking way and uses a blocking library for a slow outside service, at 300 requests a second and 150 ms each. Which model fits best?",
   "options": ["Non-blocking `Uni` endpoints on the IO thread", "The io_uring transport, because it is faster", "Plain blocking endpoints on the worker pool, or `@RunOnVirtualThread`, with explicit limits on the database and the outside service", "A Netty server with blocking handlers on the event loop"],
   "answer": 2,
   "why": "The code blocks, so it must not run on an event loop, which rules out `Uni` endpoints and blocking Netty handlers. Little's law gives 300 x 0.15 = 45 requests in flight, easy for a worker pool or virtual threads. The transport doesn't change the threading model."}
 ],
 "flashcards": [
  {"front": "What does `FileChannel.transferTo` to a socket become on Linux?", "back": "`sendfile(2)`: the kernel sends pages from the page cache to the socket; the bytes never enter your process."},
  {"front": "When can't you use zero-copy for a file transfer?", "back": "When the JVM must change the bytes on the way: TLS encryption done by the JVM, or compression."},
  {"front": "`transferTo` returned fewer bytes than you asked for. What next?", "back": "Call it again from `position + sent` with the remaining count, in a loop, until everything is sent."},
  {"front": "epoll vs io_uring in one line each?", "back": "epoll: tells you which sockets are ready, then you make the IO call (readiness). io_uring: you submit the IO on a shared ring and collect completions (completion)."},
  {"front": "What happens when a virtual thread's socket read finds no data?", "back": "`NioSocketImpl` gets `EAGAIN`, registers the file descriptor with the JDK `Poller` (epoll, one-shot) and parks the virtual thread; a poller thread unparks it when data arrives."},
  {"front": "JDK 21 vs JDK 22+ (Linux) poller threads?", "back": "JDK 21: platform `Read-Poller` and `Write-Poller` (plus updater threads). JDK 22+: one platform `MasterPoller` plus virtual sub-pollers (`VTHREAD_POLLERS`)."},
  {"front": "With virtual threads, where must the concurrency limit come from?", "back": "From you: a semaphore or the client's own pool around each downstream. Virtual threads themselves limit nothing."}
 ],
 "terms": [
  {"term": "Page cache", "plain": "The kernel's in-memory copy of file pages that were read or written recently."},
  {"term": "System call", "plain": "A switch from your program into the kernel to ask for a service, such as read, write or sendfile."},
  {"term": "Zero-copy", "plain": "Moving data from a file to a socket without copying it through your process's memory."},
  {"term": "sendfile", "plain": "The Linux system call that sends file data to a socket inside the kernel."},
  {"term": "io_uring", "plain": "A Linux interface where programs submit IO requests on a shared ring and collect completions."},
  {"term": "File descriptor", "plain": "The number the kernel uses to name an open file or socket."},
  {"term": "Poller", "plain": "The JDK's internal epoll or kqueue loop that wakes virtual threads when their sockets are ready."},
  {"term": "EPOLLONESHOT", "plain": "An epoll flag: report the socket once, then stop until it is registered again."}
 ],
 "explain_back": {
  "prompt": "A teammate says \"we moved to virtual threads, so we don't need event loops anymore\". Explain what happens inside the JDK when a virtual thread blocks on a socket read, and what still needs your attention.",
  "answer": "When a virtual thread reads from a socket that has no data, the JDK's socket code does a non-blocking read, gets EAGAIN, registers the socket's file descriptor with an internal poller and parks the virtual thread. The carrier thread is free to run other virtual threads. A poller thread waits in epoll_wait on all registered sockets and unparks the virtual thread when data arrives, like a light-watcher calling a ticket. So there still is an event loop: it moved inside the JDK, which lets our code stay blocking style. On JDK 21 the pollers are platform threads; from JDK 22 on Linux they are mostly virtual threads themselves, under one platform MasterPoller. What still needs attention: virtual threads don't limit concurrency, so each downstream needs a semaphore or a pool limit; pinning (synchronized before JDK 24, native code) and CPU-heavy work can hold carriers; and in frameworks such as Quarkus the requests still arrive on Netty event loops, which must never block."
 },
 "deeper": {
  "minutes": 10,
  "body": """Dan Kegel's C10K page, from lesson 1, compared ways to serve many clients. This track has now met each family on the JVM: readiness notification with a level-triggered `Selector` (lesson 2) and Netty's native epoll transport (lessons 3 and 4); completion-based IO with io_uring (this lesson); and one thread per client with blocking IO, which virtual threads made cheap again by running a readiness loop underneath.

The JDK's poller has settings, though you should rarely need them. On JDK 21, `-Djdk.readPollers` sets the number of read pollers (a power of 2, default 1); with 4, a thread dump shows four `Read-Poller` threads. From JDK 22, `-Djdk.pollerMode` selects the mode: `1` for `SYSTEM_THREADS` (platform pollers, the JDK 21 behavior) and `2` for `VTHREAD_POLLERS`. In `VTHREAD_POLLERS` mode on Linux, the number of read pollers defaults to the highest power of 2 not above the CPU count, capped at 32, which is why this lesson's JDK 25 run showed four. JDK 27 adds a third mode, `POLLER_PER_CARRIER` (`3`), while the Linux default stays `VTHREAD_POLLERS`.

Two smaller facts complete the picture. The JDK's `Selector` registers sockets level-triggered, while the poller uses one-shot registration: a selector serves the same socket again and again, while the poller wakes exactly one parked thread exactly once. And file IO is different from socket IO: a virtual thread reading a file does not go through the poller. As the virtual threads track explained, file operations hold the carrier while they run, which is one more reason zero-copy file sending is worth knowing about.

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
