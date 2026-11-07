# Non-blocking IO and event loops on the JVM (state as of 2026-11-07)

Scope: a 5-lesson track for a senior Kotlin/Java backend engineer who builds Quarkus services. Versions pinned by the course: JDK 25 (current LTS), Netty 4.2.20.Final, Vert.x 5.2.3, Quarkus 3.x (latest tag found: 3.40.1). Labs compile at `--release 21` (see `labs/build.gradle.kts`).

How to read these notes:
- Version tags in square brackets mark version-specific facts, e.g. [JDK 21], [JDK 22+], [Netty 4.2], [Vert.x 5], [Quarkus 3.40.1].
- **UNVERIFIED** marks anything I could not check against a fetched primary source. These are mostly from memory because a host was blocked.
- "(local run)" marks output I produced myself on this machine: OpenJDK 21.0.12.1, 4 CPUs, Linux 6.18.44, x86_64. All demo programs were compiled and run against `netty-all 4.2.20.Final` and `vertx-core 5.2.3`, resolved from Maven Central. Demo sources live in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/demos/`. That is a scratch location and may not persist, so the core code shapes are reproduced below.
- Network limits during research: kegel.com, openjdk.org (JEP pages), netty.io, vertx.io, quarkus.io and docs.oracle.com were all unreachable (blocked, DNS failure). GitHub (raw files and `git clone`) and Maven Central worked. Everything below therefore comes from project source, docs in the source repos, commit history, and local runs.

Current versions, confirmed via `git ls-remote --tags` on 2026-11-07:
- Netty: latest 4.x tag `netty-4.2.20.Final`. Its release commit `4fb6a5f` is dated 2026-11-02. Netty 5 is still alpha (latest tag `netty-5.0.0.Alpha5`). — [netty/netty tags](https://github.com/netty/netty)
- Vert.x: latest tag `5.2.3` (5.1.x is at 5.1.10). — [eclipse-vertx/vert.x tags](https://github.com/eclipse-vertx/vert.x)
- Quarkus: latest tag `3.40.1`. — [quarkusio/quarkus tags](https://github.com/quarkusio/quarkus)
- JDK: `jdk25u` is at 25.0.6, with `DEFAULT_VERSION_DATE=2027-01-19`. `jdk27u` exists (27.0.2 in progress). Mainline `jdk` is JDK 28 (`DEFAULT_VERSION_FEATURE=28`, date 2027-03-23). So in Nov 2026, JDK 27 is the latest feature release and JDK 25 is the LTS. — [jdk25u version-numbers.conf](https://raw.githubusercontent.com/openjdk/jdk25u/master/make/conf/version-numbers.conf); [jdk27u version-numbers.conf](https://raw.githubusercontent.com/openjdk/jdk27u/master/make/conf/version-numbers.conf); [jdk master version-numbers.conf](https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf)

---

## Q1. Blocking IO, thread-per-connection, and the C10K problem

### Takeaway
With blocking IO, a thread waiting on a socket can do nothing else. Serving N concurrent connections therefore needs about N threads, and that stops scaling on memory and context switches. Dan Kegel's C10K page (1999 onward) catalogued the alternative: few threads, non-blocking sockets and readiness notification (select/poll, then epoll/kqueue). That is the design behind java.nio, Netty, Vert.x and, under the hood, the JDK's virtual-thread poller.

### Cited Findings
- Vert.x's core docs state the problem directly: "With a conventional blocking API the calling thread might block when: Reading data from a socket; Writing data to disk; Sending a message to a recipient and waiting for a reply... when your thread is waiting for a result it can't do anything else - it's effectively useless... if you want a lot of concurrency using blocking APIs then you need a lot of threads... Threads have overhead in terms of the memory they require (e.g. for their stack) and in context switching. For the levels of concurrency required in many modern applications, a blocking approach just doesn't scale." — [Vert.x 5.2.3 core docs, "Don't block me!"](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- The Quarkus reactive architecture guide describes the imperative model the same way: "The thread is blocked, waiting for the result of the I/O. To handle concurrent requests, you need multiple threads, so, you need to introduce a worker thread pool". In contrast, "non-blocking I/O avoids that problem. A few threads can handle many concurrent I/O." — [quarkus-reactive-architecture.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc)
- Vert.x names the pattern "Reactor Pattern" (single event loop, as in Node.js). Vert.x's own variant, with several event loops per process, is the "Multi-Reactor Pattern". — [Vert.x 5.2.3 core docs, "Reactor and Multi-Reactor"](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- Quarkus calls its dispatch model a proactor pattern: "Quarkus implements a proactor pattern that switches to worker thread when needed." — [quarkus-reactive-architecture.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc)
- **UNVERIFIED (kegel.com blocked, from memory):** The C10K page is by Dan Kegel, first written in 1999. Its opening reads roughly "It's time for web servers to handle ten thousand clients simultaneously, don't you think? After all, the web is a big place now." It lists I/O strategies roughly as follows:
  1. Serve many clients with each thread, using non-blocking I/O and **level-triggered** readiness notification (select/poll, /dev/poll).
  2. The same with **readiness change (edge-triggered)** notification (kqueue, epoll in ET mode, realtime signals).
  3. Many clients per thread with **asynchronous I/O** (aio_*, completion notification).
  4. **One client per thread** with blocking I/O.
  5. Build the server into the kernel.

  It also discusses the per-thread stack memory limits of the era. Lesson writers should re-check the wording at http://www.kegel.com/c10k.html before quoting it.

### Inferences
- The modern framing for the lesson: Kegel's strategies 1 and 2 are the java.nio Selector (level-triggered epoll) and Netty's native epoll transport (Netty's epoll transport is edge-triggered by default: **UNVERIFIED**, not checked in 4.2 source). Strategy 3 is io_uring (Netty 4.2 `IoUringIoHandler`). Strategy 4 is classic thread-per-request, which virtual threads make cheap again because the JDK runs a strategy-1/2 poller underneath (see Q3).

### Gaps
- Could not fetch the C10K page, so exact quotes and the strategy list are unverified.

---

## Q2. java.nio basics: ByteBuffer, channels, Selector, SelectionKey, the select loop, partial reads/writes, OP_WRITE pitfalls

### Takeaway
A `ByteBuffer` is a cursor over memory: you write with `put`, `flip()` to read, then `compact()` or `clear()` to write again. Non-blocking socket `read`/`write` move only as many bytes as the kernel buffer allows, so partial reads and writes are normal and must be handled. A `Selector` reports readiness, level-triggered on Linux. You must remove handled keys from the selected-key set yourself. If you register `OP_WRITE` permanently, the loop busy-spins, because a socket with buffer space is always writable.

### Cited Findings
**ByteBuffer state machine (local run of `BufferDemo`, JDK 21):**
```
allocate(16)           pos=0  lim=16 cap=16 remaining=16
put("hello")           pos=5  lim=16 cap=16 remaining=11
flip()                 pos=0  lim=5  cap=16 remaining=5
get(2) -> "he"         pos=2  lim=5  cap=16 remaining=3
compact()              pos=3  lim=16 cap=16 remaining=13   <- unread "llo" moved to index 0, ready to append
put("XY")              pos=5  lim=16 cap=16 remaining=11
flip()                 pos=0  lim=5  cap=16 remaining=5
readable content: "lloXY"
clear()                pos=0  lim=16 cap=16 remaining=16
heap  : isDirect=false hasArray=true java.nio.HeapByteBuffer order=BIG_ENDIAN
direct: isDirect=true hasArray=false java.nio.DirectByteBuffer
forgot flip(): remaining()=6 -> a write would send 6 stale bytes, not the 2 you put
```
(local run)

**Direct vs heap:**
- ByteBuffer Javadoc [JDK 25u source]: direct buffers "typically have somewhat higher allocation and deallocation costs than non-direct buffers. The contents of direct buffers may reside outside of the normal garbage-collected heap, and so their impact upon the memory footprint of an application might not be obvious. It is therefore recommended that direct buffers be allocated primarily for large, long-lived buffers that are subject to the underlying system's native I/O operations." — [X-Buffer.java.template (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/X-Buffer.java.template)
- When you pass a **heap** buffer to a channel read or write, the JDK copies through a temporary direct buffer: `IOUtil.write` calls `Util.getTemporaryDirectBuffer(rem)` and then `bb.put(src)`. Reads go through the same temporary direct buffer. So heap buffers cost one extra copy per IO, and direct buffers avoid it. — [sun/nio/ch/IOUtil.java (jdk master)](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/IOUtil.java)
- A crude allocation loop (200k × 1 KiB, not JMH) was inconclusive. Round 0: heap 100 ms, direct 594 ms. Round 1: heap 292 ms, direct 171 ms. JIT and GC noise dominates. Use JMH if a lesson wants numbers. (local run)

**Channel semantics (Javadoc, JDK 25u source):**
- `WritableByteChannel.write`: "Some types of channels, depending upon their state, may write only some of the bytes or possibly none at all. A socket channel in non-blocking mode, for example, cannot write any more bytes than are free in the socket's output buffer." — [WritableByteChannel.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/WritableByteChannel.java)
- `ReadableByteChannel.read`: "A socket channel in non-blocking mode, for example, cannot read any more bytes than are immediately available from the socket's input buffer". It returns -1 at end-of-stream. — [ReadableByteChannel.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/ReadableByteChannel.java)

**Selector / SelectionKey (Javadoc, JDK 25u source):**
- "Keys are added to the selected-key set by selection operations. A key may be removed directly from the selected-key set by invoking the set's remove method or by invoking the remove method of an iterator obtained from the set... Keys may not be added directly to the selected-key set." — [Selector.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java)
- Thread safety: "A Selector and its key set are safe for use by multiple concurrent threads. Its selected-key set and cancelled-key set, however, are not." — [Selector.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java)
- "The *interest set* determines which operation categories will be tested for readiness the next time one of the selector's selection methods is invoked." "The *ready set* identifies the operation categories for which the key's channel has been detected to be ready by the key's selector. The ready set is initialized to zero when the key is created; it may later be updated by the selector during a selection operation, but it cannot be updated directly." — [SelectionKey.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/SelectionKey.java)

**Minimal correct select loop (core of `NioEcho.java`, ran on JDK 21):**
```java
static final class Conn { final ByteBuffer buf = ByteBuffer.allocateDirect(16 * 1024); boolean eof; }
while (true) {
  sel.select();
  Iterator<SelectionKey> it = sel.selectedKeys().iterator();
  while (it.hasNext()) {
    SelectionKey k = it.next(); it.remove();                 // you remove handled keys
    if (!k.isValid()) continue;
    if (k.isAcceptable()) {
      SocketChannel ch = ((ServerSocketChannel) k.channel()).accept();
      if (ch == null) continue;
      ch.configureBlocking(false);
      ch.register(sel, OP_READ, new Conn());
      continue;
    }
    SocketChannel ch = (SocketChannel) k.channel(); Conn c = (Conn) k.attachment();
    try {
      if (k.isReadable()) { if (ch.read(c.buf) < 0) c.eof = true; }  // partial read: whatever is there
      c.buf.flip(); if (c.buf.hasRemaining()) ch.write(c.buf);       // partial write: maybe only some bytes
      c.buf.compact();                                                // keep the unwritten tail
      boolean pending = c.buf.position() > 0;
      if (c.eof && !pending) { ch.close(); continue; }
      int ops = 0;
      if (!c.eof && c.buf.hasRemaining()) ops |= OP_READ;            // buffer full -> stop reading (backpressure)
      if (pending) ops |= OP_WRITE;                                   // OP_WRITE only while data is pending
      k.interestOps(ops);
    } catch (IOException e) { k.cancel(); ch.close(); }
  }
}
```
Output with an 8 MiB echo, client `SO_RCVBUF=4096`, client writing and reading on separate threads:
```
Selector impl = sun.nio.ch.EPollSelectorImpl, provider = sun.nio.ch.EPollSelectorProvider
listening on 127.0.0.1:42413 (ephemeral)
echoed 8388608/8388608 bytes, identical=true, 152 ms
server: selects=537 reads=531 partialWrites=8 OP_WRITE armed 4 times; client read() calls=2044
idle 300 ms, interest OP_READ only           : select() returned >0 0 times
idle 300 ms, interest OP_READ|OP_WRITE always: select() returned >0 94243 times  <- busy spin
```
(local run). Counts vary run to run: a second run gave partialWrites=4, OP_WRITE armed 1 time, and 24,556 spins under strace. The "0 vs tens of thousands" contrast is stable.

- The OP_WRITE spin shows directly in syscalls. Under `strace -f -c`, that run made 25,097 `epoll_wait` calls against 10 `epoll_ctl` and 3 `epoll_create1`. (local run)
- The client must read concurrently with writing. With a single-threaded write-everything-then-read client, both sides' socket buffers fill and the echo deadlocks. That is why the demo uses a writer thread. (local run design; a classic pitfall)

### Inferences
- Lab-relevant invariants: (1) never assume one `read` equals one message; frame it (length prefix or delimiter). (2) Keep unwritten bytes and arm OP_WRITE only while they exist. (3) Stop reading (clear OP_READ) when your outbound buffer is full. That is backpressure. (4) Remove keys from `selectedKeys()`.
- Selector key sets are not safe to share. The safe pattern is single-threaded ownership of a selector, which is exactly Netty's "one thread per EventLoop" rule.

### Gaps
- I did not fetch the `SocketChannel` and `ByteBuffer` Javadoc HTML pages (docs.oracle.com blocked). Quotes come from the JDK 25u source files that generate them.

---

## Q3. How the JDK maps selectors to epoll/kqueue, and how a blocking socket read in a virtual thread works (JDK 21 vs 25 and later)

### Takeaway
On Linux, `Selector.open()` returns `sun.nio.ch.EPollSelectorImpl`, which uses level-triggered epoll. On macOS it is kqueue. A virtual thread that blocks in `Socket.read()` doesn't block its carrier. `NioSocketImpl` puts the fd in non-blocking mode, and on EAGAIN it registers the fd with a JDK-internal **Poller** (epoll, one-shot) and parks the virtual thread. The poller unparks it when the fd is ready.
- [JDK 21]: pollers are dedicated platform threads (`Read-Poller`, `Write-Poller`, plus `Read-Updater`/`Write-Updater` on Linux).
- [JDK 22+, including JDK 25 LTS]: on Linux the default is `VTHREAD_POLLERS`. One platform `MasterPoller` thread plus N **virtual** `SubPoller-*` threads, scheduled like other virtual threads.
- [JDK 27+]: adds an optional `POLLER_PER_CARRIER` mode. The default stays `VTHREAD_POLLERS`.

### Cited Findings
**Selector mapping:**
- Linux `DefaultSelectorProvider` returns an `EPollSelectorProvider`. Confirmed at runtime: `sun.nio.ch.EPollSelectorImpl` / `sun.nio.ch.EPollSelectorProvider`. — [linux DefaultSelectorProvider.java (jdk master)](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/DefaultSelectorProvider.java); (local run)
- macOS: `private static final SelectorProviderImpl INSTANCE = new KQueueSelectorProvider();` — [macosx DefaultSelectorProvider.java (jdk master)](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/macosx/classes/sun/nio/ch/DefaultSelectorProvider.java)
- `EPollSelectorImpl` [JDK 25u] polls with `EPoll.wait(epfd, pollArrayAddress, NUM_EPOLLEVENTS, to)`, where `NUM_EPOLLEVENTS = Math.min(IOUtil.fdLimit(), 1024)` ("maximum number of events to poll in one call to epoll_wait"). The file contains no `EPOLLET` or `EPOLLONESHOT`, so registrations are level-triggered. — [EPollSelectorImpl.java (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/EPollSelectorImpl.java)
- strace of the NIO echo demo shows only `epoll_create1`, `epoll_ctl` and `epoll_wait`. (local run)
- Windows selector implementation: **UNVERIFIED** (not fetched). I believe it is `WEPollSelectorImpl` (wepoll) since JDK 19.

**Virtual-thread blocking path, JDK 21 (observed):** jcmd stack of a virtual thread blocked in `Socket.getInputStream().read()`:
```
#20 "" virtual
      java.base/java.lang.VirtualThread.park(VirtualThread.java:596)
      java.base/java.lang.System$2.parkVirtualThread(System.java:2644)
      java.base/jdk.internal.misc.VirtualThreads.park(VirtualThreads.java:54)
      java.base/java.util.concurrent.locks.LockSupport.park(LockSupport.java:369)
      java.base/sun.nio.ch.Poller.pollIndirect(Poller.java:139)
      java.base/sun.nio.ch.Poller.poll(Poller.java:102)
      java.base/sun.nio.ch.Poller.poll(Poller.java:87)
      java.base/sun.nio.ch.NioSocketImpl.park(NioSocketImpl.java:175)
      java.base/sun.nio.ch.NioSocketImpl.park(NioSocketImpl.java:201)
      java.base/sun.nio.ch.NioSocketImpl.implRead(NioSocketImpl.java:309)
      java.base/sun.nio.ch.NioSocketImpl.read(NioSocketImpl.java:346)
      java.base/sun.nio.ch.NioSocketImpl$1.read(NioSocketImpl.java:796)
      java.base/java.net.Socket$SocketInputStream.read(Socket.java:1099)
```
The poller thread itself sits in epoll:
```
#1456 "Read-Poller"
      java.base/sun.nio.ch.EPoll.wait(Native Method)
      java.base/sun.nio.ch.EPollPoller.poll(EPollPoller.java:74)
      java.base/sun.nio.ch.Poller.poll(Poller.java:370)
      java.base/sun.nio.ch.Poller.pollLoop(Poller.java:277)
```
With 2,000 virtual threads each blocked on its own socket read, the platform threads were `4 x ForkJoinPool-1-worker-N` (carriers, equal to the CPU count), `1 x Read-Poller`, `1 x Write-Poller`, `1 x Read-Updater`, `1 x Write-Updater`, plus JVM housekeeping and `main`/`acceptor`: 15 platform threads total. jcmd showed 2,000 virtual-thread entries. After one byte was written to every socket, all 2,000 unparked and finished in 112 ms. With `-Djdk.readPollers=4` there were `4 x Read-Poller`. (local run, JDK 21.0.12.1)

**Poller source, JDK 21u:**
- Class doc: "Polls file descriptors. Virtual threads invoke the poll method to park until a given file descriptor is ready for I/O." The poller keeps a `Map<Integer, Thread>` from fd to parked thread. It has two registration strategies: `pollDirect`, which registers and then parks, and `pollIndirect`, which "queues the file descriptor to the update thread, then parks". These are chosen by `jdk.useDirectRegister` or the provider default. The Linux provider in 21u does not override that default, which matches the `Read-Updater` thread and the `pollIndirect` frame seen above. — [Poller.java (jdk21u)](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/sun/nio/ch/Poller.java); [linux DefaultPollerProvider (jdk21u)](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java)
- Poller count comes from `jdk.readPollers` / `jdk.writePollers`, default "1", and must be a power of 2. Pollers are started as `InnocuousThread.newSystemThread(prefix + "-Poller", ...)`. — [Poller.java (jdk21u)](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/sun/nio/ch/Poller.java)

**The JDK 22 change: poller threads can be virtual threads.**
- OpenJDK commit `c099cf53`, 2023-11-04, Alan Bateman: "8318422: Allow poller threads be virtual threads". `jdk21u` has no `Poller.Mode`. `jdk22u` has `VTHREAD_POLLERS`, so this first shipped in **JDK 22**. — [openjdk/jdk commit c099cf53](https://github.com/openjdk/jdk/commit/c099cf53) (read via git clone); [Poller.java (jdk22u)](https://raw.githubusercontent.com/openjdk/jdk22u/master/src/java.base/share/classes/sun/nio/ch/Poller.java)
- `Poller.Mode` Javadoc [JDK 25u]:
  - `SYSTEM_THREADS`: "ReadPoller and WritePoller are dedicated platform threads that block waiting for events and unpark virtual threads when file descriptors are ready for I/O."
  - `VTHREAD_POLLERS`: "ReadPoller and WritePoller threads are virtual threads that poll for events, yielding between polls and unparking virtual threads when file descriptors are ready for I/O. If there are no events then the poller threads park until there are I/O events to poll. This mode helps to integrate polling with virtual thread scheduling. The approach is similar to the default scheme in 'User-level Threading: Have Your Cake and Eat It Too' by Karsten and Barghi 2020."

  — [Poller.java (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java)
- Startup in `VTHREAD_POLLERS` mode [JDK 25u]: `startPlatformThread("MasterPoller", masterPoller::pollerLoop)`, then sub-pollers on `Thread.ofVirtual().name("SubPoller-", 0)`, each running `p.subPollerLoop(masterPoller)` for both read and write pollers. `SYSTEM_THREADS` mode starts platform `Read-Poller` / `Write-Poller` threads. The mode can be forced with `-Djdk.pollerMode=SYSTEM_THREADS|1` or `VTHREAD_POLLERS|2`. Sub-poller doc: "The sub-poller registers its file descriptor with the master poller to park until there are events to poll... The sub-poller yields after each poll". — [Poller.java (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java)
- Linux defaults [JDK 22–26, identical in 22u and 25u]: `defaultPollerMode()` returns `VTHREAD_POLLERS` if `ContinuationSupport.isSupported()`, else `SYSTEM_THREADS`. Read-poller count is `min(Integer.highestOneBit(ncpus), 32)` in `VTHREAD_POLLERS` mode, else `max(Integer.highestOneBit(ncpus / 4), 1)`. — [linux DefaultPollerProvider (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java); [linux DefaultPollerProvider (jdk22u)](https://raw.githubusercontent.com/openjdk/jdk22u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java)
- macOS [JDK 25u]: the provider only supplies `KQueuePoller`s and does not override `defaultPollerMode()`. The base-class `@implSpec` says "The default implementation uses system threads", so macOS stays on platform poller threads. — [macosx DefaultPollerProvider (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/macosx/classes/sun/nio/ch/DefaultPollerProvider.java); [PollerProvider.java (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/PollerProvider.java)
- `Poller.java` is byte-identical in `jdk24u` and `jdk25u`. JDK 25 brought no poller change over 24. — [Poller.java (jdk24u)](https://raw.githubusercontent.com/openjdk/jdk24u/master/src/java.base/share/classes/sun/nio/ch/Poller.java) vs [jdk25u](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java) (diffed locally)
- The virtual-thread poller registers fds with `EPOLLONESHOT` (`EPoll.ctl(epfd, EPOLL_CTL_MOD, fdVal, (event | EPOLLONESHOT))`) [jdk master]. — [EPollPoller.java (jdk master)](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/EPollPoller.java)

**JDK 24 additions relevant here:**
- `8337199: Add jcmd Thread.vthread_scheduler and Thread.vthread_pollers diagnostic commands` (commit `5c8cb2ed`, 2024-12-03). `vthread_pollers` is present in `diagnosticCommand.hpp` in both jdk24u and jdk25u. This gives a JDK 24+/25 lesson a way to inspect pollers. — [openjdk/jdk commit 5c8cb2ed](https://github.com/openjdk/jdk/commit/5c8cb2ed) (via git); [diagnosticCommand.hpp (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/hotspot/share/services/diagnosticCommand.hpp)
- JEP 491 (`8338383: Implement JEP 491: Synchronize Virtual Threads without Pinning`, commit `78b80150`, 2024-11-12). Quarkus docs: "Starting with Java 24... `synchronized` blocks and methods no longer cause pinning... However, native code interactions can still cause pinning", and "The `-Djdk.tracePinnedThreads` system property is no longer available starting with Java 24". — [openjdk/jdk commit 78b80150](https://github.com/openjdk/jdk/commit/78b80150) (via git); [Quarkus virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc)

**After JDK 25 (for context; not the LTS):**
- `8374170: I/O Poller updates` (commit `cd5256d5`, 2026-02-06, Alan Bateman). `jdk27u` and master have a third mode, `POLLER_PER_CARRIER` ("Read pollers are per-carrier virtual threads that poll for events... The write poller is a system-wide platform thread."), selectable with `jdk.pollerMode=3`. `jdk26u` doesn't have it. The JDK 27 Linux default is still `VTHREAD_POLLERS`. — [openjdk/jdk commit cd5256d5](https://github.com/openjdk/jdk/commit/cd5256d5) (via git); [Poller.java (jdk27u)](https://raw.githubusercontent.com/openjdk/jdk27u/master/src/java.base/share/classes/sun/nio/ch/Poller.java); [Poller.java (jdk26u)](https://raw.githubusercontent.com/openjdk/jdk26u/master/src/java.base/share/classes/sun/nio/ch/Poller.java); [linux DefaultPollerProvider (jdk27u)](https://raw.githubusercontent.com/openjdk/jdk27u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java)
- `8394217: Allow poller group be configured to have no write pollers` (commit `dfebf8c5`, 2026-10-13). This is on master, i.e. JDK 28. — [openjdk/jdk commit dfebf8c5](https://github.com/openjdk/jdk/commit/dfebf8c5) (via git)

### Inferences
- Teaching line: "A virtual thread's blocking `read()` is a non-blocking read plus park/unpark driven by an epoll loop inside the JDK." Virtual threads don't remove the event loop. They hide it in `sun.nio.ch.Poller`.
- JDK 21 vs 25, by thread names in a thread dump: 21 shows `Read-Poller`/`Write-Poller` platform threads, and on Linux also `*-Updater`. 25 on Linux should show a `MasterPoller` platform thread plus virtual `SubPoller-N` threads. That 25 claim is inferred from source; I could not run JDK 25 here.
- I infer from timing (commit between the 26 and 27 forks) that the `POLLER_PER_CARRIER` mode came with 8374170. I did not read the diff.

### Gaps
- No JDK 25 binary was available locally, so JDK 25 thread names and counts are from source, not observed. A lesson writer with JDK 25 should run `VThreadPoller` and `jcmd <pid> Thread.vthread_pollers` to capture real output.
- JEP 444 / JEP 491 pages could not be fetched (openjdk.org blocked). JEP facts above come from commit titles and the Quarkus guide.

---

## Q4. Netty 4.2: EventLoopGroup/EventLoop, Channel, pipeline, handlers, ByteBuf and reference counting, leak detection, offloading, and what changed in 4.2

### Takeaway
[Netty 4.2] Construct event loops as `new MultiThreadIoEventLoopGroup(<n>, <Transport>IoHandler.newFactory())`. `NioEventLoopGroup`, `EpollEventLoopGroup` and friends are deprecated. Each `EventLoop` is a single thread, and a `Channel` stays registered to one loop for life. Inbound `ByteBuf`s are reference-counted: whoever handles a message last releases it. `SimpleChannelInboundHandler` does that for you. Leak detection samples about 1/128 of buffers by default (`SIMPLE`). `PARANOID` tracks every buffer and is meant for tests. Also new in 4.2:
- The adaptive allocator is the default.
- io_uring graduated to a first-class transport.
- The per-handler `EventExecutorGroup` overloads of `ChannelPipeline.add*` are deprecated. Netty now says to dispatch blocking work manually.

### Cited Findings
**4.2 API shape and migration (official migration guide in the Netty wiki):**
- "All transport-specific event loop groups, such as `NioEventLoopGroup`, have been deprecated. Integrators should now instead pass a transport-specific `IoHandlerFactory` to a `MultiThreadedEventLoopGroup` constructor." Example: `EventLoopGroup group = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory()); // ✅` versus `new NioEventLoopGroup(); // ❌`. The factories are `NioIoHandler.newFactory()`, `EpollIoHandler.newFactory()`, `KQueueIoHandler.newFactory()`, `IoUringIoHandler.newFactory()` and `LocalIoHandler.newFactory()`. "Note that you must still configure the relevant channel or channel factory in your Bootstrap or ServerBootstrap instances." — [Netty 4.2 Migration Guide](https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md)
- The guide writes `MultiThreadedEventLoopGroup` in prose, but the class is `io.netty.channel.MultiThreadIoEventLoopGroup`. Its 4.2.20 public constructors (javap):
  - `(IoHandlerFactory)`
  - `(int, IoHandlerFactory)`
  - `(ThreadFactory, IoHandlerFactory)`
  - `(Executor, IoHandlerFactory)`
  - `(int, Executor, IoHandlerFactory)`
  - `(int, ThreadFactory, IoHandlerFactory)`
  - `(int, Executor, EventExecutorChooserFactory, IoHandlerFactory)`

  — [netty-transport-4.2.20.Final.jar](https://repo.maven.apache.org/maven2/io/netty/netty-transport/4.2.20.Final/) (javap, local); [MultiThreadIoEventLoopGroup.java (4.2 branch)](https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/MultiThreadIoEventLoopGroup.java)
- `NioIoHandler.newFactory()` overloads: `()`, `(SelectorProvider)`, `(SelectorProvider, SelectStrategyFactory)`. `IoUringIoHandler.newFactory()` overloads: `()`, `(int)`, `(IoUringIoHandlerConfig)`. (javap, local)
- Compiling `new NioEventLoopGroup()` against 4.2.20 with `-Xlint:deprecation` gives `warning: [deprecation] NioEventLoopGroup in io.netty.channel.nio has been deprecated`. The Javadoc reads `@deprecated Use MultiThreadIoEventLoopGroup with NioIoHandler#newFactory().` — (local run); [NioEventLoopGroup.java (4.2)](https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/nio/NioEventLoopGroup.java)
- Default thread count is `DEFAULT_EVENT_LOOP_THREADS = Math.max(1, SystemPropertyUtil.getInt("io.netty.eventLoopThreads", NettyRuntime.availableProcessors() * 2))`. Observed: `executorCount() = 8` on 4 CPUs. — [netty-transport-4.2.20.Final-sources.jar, MultithreadEventLoopGroup.java](https://repo.maven.apache.org/maven2/io/netty/netty-transport/4.2.20.Final/); (local run)
- Extensibility: `MultiThreadIoEventLoopGroup` / `SingleThreadIoEventLoop` expose hooks to count registered channels, to measure "how long the IO processing vs task processing took", and to see channels processed per loop run. You can also register non-Channel `IoHandle`s, e.g. "this could be used to implement file IO with io_uring." — [Netty 4.2 Migration Guide](https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md)

**Other 4.2 compatibility changes (same guide):**
- The minimum Java version moves from 6 to 8.
- The adaptive allocator is the new default: "We believe that most workloads will observe reduced memory usage... It was also designed from the start to work well with virtual threads." Revert with `-Dio.netty.allocator.type=pooled`. Observed: `ByteBufAllocator.DEFAULT = io.netty.buffer.AdaptiveByteBufAllocator`, and `buffer(16)` returns `AdaptiveByteBuf isDirect=true`. (local run)
- TLS clients now verify hostnames by default (`endpointIdentificationAlgorithm` = `HTTPS`). The escape hatch is `-Dio.netty.handler.ssl.defaultEndpointVerificationAlgorithm=NONE`.
- `netty-codec` is split into sub-modules.
- "The pipeline call-stack has been flattened".
- Minimum glibc is 2.17.
- 4.1 and 4.2 "cannot co-exist on the class path".

— [Netty 4.2 Migration Guide](https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md)

**io_uring status [Netty 4.2]:**
- "we have *graduated* the io_uring transport from incubator, to a fully supported first-class transport module." The package changes from `io.netty.incubator.channel.uring` to `io.netty.channel.uring`. Class prefix is `IoUring` (not `IOUring`). `IOUringEventLoopGroup` is replaced by `MultiThreadIoEventLoopGroup` + `IoUringIoHandler`. io_uring requires Java 9+. — [Netty 4.2 Migration Guide](https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md)
- `IoUring` checks the kernel version at load (`Native.checkKernelVersion`). A source comment says kernels "< 5.4 which we don't support anyway". The precise minimum kernel per feature is **UNVERIFIED**. — [netty-transport-classes-io_uring-4.2.20.Final-sources.jar, IoUring.java](https://repo.maven.apache.org/maven2/io/netty/netty-transport-classes-io_uring/4.2.20.Final/)
- io_uring work is still active inside 4.2.x. 4.2.20.Final contains "IoUring:Refactor io_uring write lifecycle management (#17757)" (2026-10-29) and "Use a long file offset when splicing a DefaultFileRegion with io_uring (#18018)" (2026-10-23). Later fixes such as #18229 (2026-11-05) are not in 4.2.20. — [netty/netty 4.2 history](https://github.com/netty/netty/commits/4.2) (via git clone, `merge-base --is-ancestor` checked)
- On this machine (kernel 6.18), `Epoll.isAvailable()=true` and `IoUring.isAvailable()=true`. Echo worked over NIO, EPOLL and IO_URING. (local run)

**Threading model observed (echo demo: boss group of 1, worker group of 2):**
```
[NIO server] /127.0.0.1:45854 registered on multiThreadIoEventLoopGroup-4-1 inEventLoop=true
[NIO server] /127.0.0.1:45868 registered on multiThreadIoEventLoopGroup-4-2 inEventLoop=true
[NIO server] /127.0.0.1:45874 registered on multiThreadIoEventLoopGroup-4-1 inEventLoop=true
```
Connections are assigned to loops round-robin and handled on that loop's single thread. Epoll and io_uring runs printed the same pattern. (local run)

**Deprecation of per-handler executors [Netty 4.2.0+]:**
- Compiling `pipeline.addLast(blockingGroup, "biz", handler)` against 4.2.20 gives `warning: [deprecation] addLast(EventExecutorGroup,String,ChannelHandler) in ChannelPipeline has been deprecated`. The Javadoc reads `@deprecated use addLast(String, ChannelHandler)`. — (local run); [netty-transport-4.2.20.Final-sources.jar, ChannelPipeline.java](https://repo.maven.apache.org/maven2/io/netty/netty-transport/4.2.20.Final/)
- Commit `d64340b` (2024-12-05), "Deprecate ChannelPipeline.add*(EventExecutorGroup....) methods (#14538)": "While it seemed like a great idea to allow to run different handlers with different executors it became clear that this introduce more problems then it solves. If someone wants to run things outside of the EventLoop its much better to dispatch it manually." It first appears in tag `netty-4.2.0.RC1`. — [netty/netty commit d64340b](https://github.com/netty/netty/commit/d64340b) (via git)
- Commit `50ffe5b` (2024-12-06) deprecates `UnorderedThreadPoolEventExecutor`. Its `inEventLoop` "always returned false", which defeats Netty's event-loop fast paths, and it is slated for removal in Netty 5. — [netty/netty commit 50ffe5b](https://github.com/netty/netty/commit/50ffe5b) (via git)
- 4.2.0.Final was released 2025-04-03 (release commit `09e64d2`). — [netty/netty history](https://github.com/netty/netty/commits/4.2) (via git)

**Selector bug workaround and a 4.2.20 spin fix:**
- `NioIoHandler` still has `io.netty.selectorAutoRebuildThreshold` (default 512) and `rebuildSelector0()`, the long-standing workaround for premature selector returns (the "epoll spin bug"). — [NioIoHandler.java (4.2)](https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/nio/NioIoHandler.java)
- Commit `06518dc` (2026-10-28, in 4.2.20.Final), "Round up the NIO select timeout again to not busy spin (#18137)". `millisBeforeDeadline` rounded to the nearest millisecond, so with a timer due in under 0.5 ms "the timeout is 0, so select(...) calls selectNow() and returns... An event loop that has I/O and a pending timer therefore polls the selector in a loop". This is a real-world cousin of the OP_WRITE spin. — [netty/netty commit 06518dc](https://github.com/netty/netty/commit/06518dc) (via git)

**ByteBuf and reference counting:**
- Rule: "the party that accesses a reference-counted object last is also responsible for the destruction of that reference-counted object."
- Outbound messages "are created by your application, and it is the responsibility of Netty to release these after writing them out to the wire". Intercepting handlers such as encoders must release intermediates.
- Use `ReferenceCountUtil.release(msg)` for inbound messages you consume.

  — [Netty wiki: Reference counted objects](https://raw.githubusercontent.com/wiki/netty/netty/Reference-counted-objects.md)

  This wiki page is old in places. It names `SimpleChannelHandler` (a Netty 3 name; 4.x has `SimpleChannelInboundHandler`) and recommends `ReferenceCountUtil.releaseLater()`, which is `@deprecated` in 4.2.20: "this may introduce a lot of memory usage so it is generally preferable to manually release objects." — [netty-common-4.2.20.Final-sources.jar, ReferenceCountUtil.java](https://repo.maven.apache.org/maven2/io/netty/netty-common/4.2.20.Final/)
- Observed ByteBuf behaviour (local run):
  ```
  buffer(16): AdaptiveByteBuf isDirect=true readerIndex=0 writerIndex=0 capacity=16 maxCapacity=2147483647 refCnt=1
  after writeInt+writeLong: writerIndex=12 readableBytes=12
  after readInt: readerIndex=4 readableBytes=8 (no flip needed: separate reader/writer indexes)
  retain(): refCnt=2
  release() -> false refCnt=1
  release() -> true refCnt=0
  access after release -> IllegalReferenceCountException: refCnt: 0
  ```

**Leak detection:**
- Levels: `DISABLED`; `SIMPLE` ("tells if there is a leak or not for 1% of buffers. Default."); `ADVANCED` ("where the leaked buffer was accessed for 1% of buffers"); `PARANOID` ("Same with ADVANCED except that it's for every single buffer. Useful for automated testing phase. You could fail the build if the build output contains 'LEAK: '"). Recommended practice: "Run your unit tests and integration tests at PARANOID leak detection level, as well as at SIMPLE level". — [Netty wiki: Reference counted objects](https://raw.githubusercontent.com/wiki/netty/netty/Reference-counted-objects.md)
- Source [4.2]: `DEFAULT_LEVEL = Level.SIMPLE`; `DEFAULT_SAMPLING_INTERVAL = 128` (≈0.8%, the "1%" in the wiki); property `io.netty.leakDetection.level` (legacy `io.netty.leakDetectionLevel`); `io.netty.leakDetection.targetRecords` default 4; a `LeakListener` hook. — [ResourceLeakDetector.java (4.2)](https://raw.githubusercontent.com/netty/netty/4.2/common/src/main/java/io/netty/util/ResourceLeakDetector.java)
- Test hook: `ByteBufUtil.setLeakListener(ResourceLeakDetector.LeakListener)` exists in 4.2.20 (javap) and fires on detected ByteBuf leaks. (local run)
- Exact PARANOID report text, from a handler that neither released nor forwarded its message (local run, 4.2.20, JUL logging):
  ```
  SEVERE: LEAK: ByteBuf.release() was not called before it's garbage-collected. See https://netty.io/wiki/reference-counted-objects.html for more information.
  Recent access records:
  #1:
  	Hint: 'Netty42Demo$5#0' will handle the message from this point.
  	io.netty.channel.DefaultChannelPipeline.touch(DefaultChannelPipeline.java:115)
  	io.netty.channel.AbstractChannelHandlerContext.fireChannelRead(AbstractChannelHandlerContext.java:344)
  	io.netty.channel.DefaultChannelPipeline$HeadContext.channelRead(DefaultChannelPipeline.java:1471)
  	io.netty.channel.DefaultChannelPipeline.fireChannelRead(DefaultChannelPipeline.java:960)
  	io.netty.channel.embedded.EmbeddedChannel.writeInbound(EmbeddedChannel.java:369)
  	Netty42Demo.leak(Netty42Demo.java:127)
  #2:
  	io.netty.buffer.AdvancedLeakAwareByteBuf.writeInt(AdvancedLeakAwareByteBuf.java:569)
  	Netty42Demo.leak(Netty42Demo.java:127)
  Created at:
  	io.netty.buffer.AdaptiveByteBufAllocator.newDirectBuffer(AdaptiveByteBufAllocator.java:67)
  	io.netty.buffer.AbstractByteBufAllocator.directBuffer(AbstractByteBufAllocator.java:168)
  	...
  leak listener saw 1 leak(s): [ByteBuf]
  ```
  Ten buffers leaked through the same code path but only **one** report was produced. The detector de-duplicates identical access-record traces. (local run)
- Netty ships a BlockHound integration class (`io/netty/util/internal/Hidden$NettyBlockHoundIntegration`) in `netty-common-4.2.20.Final.jar`. BlockHound itself is a separate dependency, not checked here. — [netty-common-4.2.20.Final.jar](https://repo.maven.apache.org/maven2/io/netty/netty-common/4.2.20.Final/) (jar listing)

**Never block the event loop (measured):** one event-loop thread; client A sends `SLOW` (handler sleeps 1 s), and client B sends `FAST` 50 ms later:
```
[handler on event loop]                  FAST reply after 1060 ms: FAST handled-on=multiThreadIoEventLoopGroup-2-1
[offloaded to DefaultEventExecutorGroup] FAST reply after 4 ms:    FAST handled-on=defaultEventExecutorGroup-5-2
[blocking in handler]        event-loop lag probe = 1070 ms; SLOW reply: SLOW on multiThreadIoEventLoopGroup-2-1
[manual dispatch to app pool] event-loop lag probe = 0 ms;   SLOW reply: SLOW on app-blocking-pool
```
(local run). The "lag probe" submits a trivial task to the loop (`group.next().submit(() -> elapsed)`) and measures how long it waited. That gives a deterministic JUnit assertion. Shutting down the `DefaultEventExecutorGroup` while channels pinned to it were still closing produced a cascade of `RejectedExecutionException: event executor terminated` warnings. This is a concrete instance of the "more problems than it solves" motivation in d64340b. (local run)

The manual-dispatch pattern that 4.2 recommends (ran as shown):
```java
@Override protected void channelRead0(ChannelHandlerContext ctx, String line) {
  blockingPool.execute(() -> {                 // leave the event loop for the blocking part
    String r = work(line);                     // e.g. JDBC
    ctx.writeAndFlush(r + "\n");               // safe from any thread: Netty hops back to the channel's event loop
  });
}
```

**EmbeddedChannel:** pipeline `LineBasedFrameDecoder(64)` → `StringDecoder` → `StringEncoder` → upper-casing `SimpleChannelInboundHandler<String>`, fed in fragments (local run):
```
writeInbound("hel") -> outbound []
writeInbound("lo\nwor") -> outbound [HELLO\n]
writeInbound("ld\n") -> outbound [WORLD\n]
oversized frame -> io.netty.handler.codec.TooLongFrameException: frame length (100) exceeds the allowed maximum (64)
finish() = false
```

**Composite buffers / slices (zero-copy within Netty), local run:**
```
composite: readableBytes=11 numComponents=2 nioBufferCount=2 content=HDR:payload
after body.setByte(0,'P'): composite content=HDR:Payload (shares memory, no copy)
slice(4,3)=Pay refCnt shared with parent=1
composite.release(): header.refCnt=0 body.refCnt=0
```
`addComponents(true, header, body)` transfers ownership. Releasing the composite releases its components. `nioBufferCount=2` means a gathering write can send it without merging.

### Inferences
- Lesson recipe for Netty 4.2 code: `MultiThreadIoEventLoopGroup` + `XxxIoHandler.newFactory()` + matching `XxxServerSocketChannel`/`XxxSocketChannel` classes in the bootstrap. For blocking work, don't use `addLast(group, ...)`. Hand off to an application executor and write back with `ctx.writeAndFlush`, or hop back with `ctx.executor().execute(...)` if you need to touch handler state.
- Older material (including the Netty in Action book and the 4.1 `ChannelPipeline` Javadoc example that recommended per-handler executor groups for "time-consuming" tasks) is outdated for 4.2. That example text is not present in 4.2.20's `ChannelPipeline.java` (grep found no "time-consuming").

### Gaps
- netty.io (user guide, release news) was unreachable. Release-level facts come from commit history and the wiki migration guide.
- Whether Netty's native epoll transport uses edge-triggered mode by default in 4.2 was not verified.
- The minimum kernel for io_uring per feature was not verified.

---

## Q5. Vert.x 5: event loops, the golden rule, blocked-thread checker, executeBlocking, worker verticles, futures-only API

### Takeaway
[Vert.x 5.2.3, which runs on Netty 4.2.20] Vert.x runs handlers on a small set of event loops. The default is `2 × CPUs`. A given handler or verticle always runs on the same loop and never concurrently. If a loop is busy longer than `maxEventLoopExecuteTime` (default 2 s), the blocked-thread checker, which runs every 1 s, logs `Thread vert.x-eventloop-thread-N has been blocked for X ms, time limit is 2000 ms`. Past `warningExceptionTime` (default 5 s) it adds a stack trace. Blocking work goes to `executeBlocking(Callable)` or to a `ThreadingModel.WORKER` / `VIRTUAL_THREAD` verticle. Vert.x 5 removed the callback overloads; async methods return `Future`.

### Cited Findings
- Golden rule, verbatim: "If you do that, then that event loop will not be able to do anything else while it's blocked. If you block all of the event loops in Vertx instance then your application will grind to a complete halt!" The examples of blocking it lists: `Thread.sleep()`, waiting on a lock, waiting on a mutex or monitor (`synchronized`), "Doing a long lived database operation and waiting for a result", a complex calculation, "Spinning in a loop". It also gives a budget example: "If you have a single event loop, and you want to handle 10000 http requests per second, then it's clear that each request can't take more than 0.1 ms to process". — [Vert.x 5.2.3 core docs, "The Golden Rule"](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- "Even though a Vertx instance maintains multiple event loops, any particular handler will never be executed concurrently, and in most cases (with the exception of worker verticles) will always be called using the *exact same event loop*." — [Vert.x 5.2.3 core docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- The docs' sample warning, `Thread vertx-eventloop-thread-3 has been blocked for 20458 ms`, is illustrative. The real 5.2.3 message is built in `BlockedThreadChecker.defaultBlockedThreadHandler`: `"Thread " + bte.thread().getName() + " has been blocked for " + (duration/1_000_000) + " ms, time limit is " + (maxExecTime/1_000_000) + " ms"`. It is logged with `log.warn(message)` when the duration is ≤ `warningExceptionTime`, otherwise with `new VertxException("Thread blocked")` carrying the blocked thread's stack. The class lives in `io.vertx.core.internal.threadchecker`. — [vertx-core-5.2.3-sources.jar](https://repo.maven.apache.org/maven2/io/vertx/vertx-core/5.2.3/)
- **Exact output** with default `Vertx.vertx()` and `runOnContext(v -> Thread.sleep(6000))` (local run, Vert.x 5.2.3, JUL default logging):
  ```
  [handler] Thread.sleep(6000) on vert.x-eventloop-thread-0
  Nov 07, 2026 5:03:55 PM io.vertx.core.impl.BlockedThreadChecker
  WARNING: Thread vert.x-eventloop-thread-0 has been blocked for 2703 ms, time limit is 2000 ms
  Nov 07, 2026 5:03:56 PM io.vertx.core.impl.BlockedThreadChecker
  WARNING: Thread vert.x-eventloop-thread-0 has been blocked for 3704 ms, time limit is 2000 ms
  Nov 07, 2026 5:03:57 PM io.vertx.core.impl.BlockedThreadChecker
  WARNING: Thread vert.x-eventloop-thread-0 has been blocked for 4706 ms, time limit is 2000 ms
  Nov 07, 2026 5:03:58 PM io.vertx.core.impl.BlockedThreadChecker
  WARNING: Thread vert.x-eventloop-thread-0 has been blocked for 5707 ms, time limit is 2000 ms
  io.vertx.core.VertxException: Thread blocked
  	at java.base/java.lang.Thread.sleep0(Native Method)
  	at java.base/java.lang.Thread.sleep(Thread.java:509)
  	at VertxDemo.lambda$sleep$0(VertxDemo.java:23)
  	at io.vertx.core.internal.ContextInternal.dispatch(ContextInternal.java:258)
  	at io.vertx.core.internal.ContextInternal.dispatch(ContextInternal.java:240)
  	at io.vertx.core.internal.ContextInternal.lambda$runOnContext$0(ContextInternal.java:51)
  	at io.netty.util.concurrent.AbstractEventExecutor.runTask(AbstractEventExecutor.java:148)
  	at io.netty.util.concurrent.AbstractEventExecutor.safeExecute(AbstractEventExecutor.java:141)
  	at io.netty.util.concurrent.SingleThreadEventExecutor.runAllTasks(SingleThreadEventExecutor.java:535)
  	at io.netty.channel.SingleThreadIoEventLoop.run(SingleThreadIoEventLoop.java:228)
  	at io.netty.util.concurrent.SingleThreadEventExecutor$5.run(SingleThreadEventExecutor.java:1214)
  	...
  [handler] woke up
  ```
  Notes:
  - The JUL logger category is still `io.vertx.core.impl.BlockedThreadChecker`, even though the class moved packages. Use that name to configure or capture the log.
  - The warning repeats once per check interval.
  - The first warning appears 2–3 s in, depending on check-interval phase.
  - The stack trace appears once the block passes 5 s.
  - The frames show a Vert.x 5 event loop is a Netty 4.2 `SingleThreadIoEventLoop`.

  (local run)
- **UNVERIFIED (from memory):** Vert.x 4 printed `Thread Thread[vert.x-eventloop-thread-0,5,main] has been blocked for ...` because it used `Thread.toString()`. Vert.x 5.2.3 uses `getName()` (verified above).
- Defaults [5.2.3] (local run reading `VertxOptions` constants):
  - `DEFAULT_EVENT_LOOP_POOL_SIZE=8` on 4 CPUs (source: `2 * CpuCoreSensor.availableProcessors()`)
  - `DEFAULT_WORKER_POOL_SIZE=20`
  - `DEFAULT_MAX_EVENT_LOOP_EXECUTE_TIME=2000000000 NANOSECONDS`
  - `DEFAULT_MAX_WORKER_EXECUTE_TIME=60000000000 NANOSECONDS`
  - `DEFAULT_BLOCKED_THREAD_CHECK_INTERVAL=1000 MILLISECONDS`
  - warning-exception time `5000000000 NANOSECONDS`. The `DEFAULT_WARNING_EXCEPTION_TIME` field is **private** in 5.2.3 (compile error), so read it via `new VertxOptions().getWarningExceptionTime()`.
  - `DEFAULT_INTERNAL_BLOCKING_POOL_SIZE = 20`

  — [vertx-core-5.2.3 VertxOptions](https://repo.maven.apache.org/maven2/io/vertx/vertx-core/5.2.3/); (local run)
- Vert.x 5.2.3's dependency BOM pins `<netty.version>4.2.20.Final</netty.version>`. — [vertx-dependencies-5.2.3.pom](https://repo.maven.apache.org/maven2/io/vertx/vertx-dependencies/5.2.3/)
- `executeBlocking` docs: "you get a future completed with the result of the blocking code execution". "Blocking code should block for a reasonable amount of time (i.e no more than a few seconds)... When the blocking operation lasts more than the 10 seconds, a message will be printed on the console by the blocked thread checker." "By default, if executeBlocking is called several times from the same context (e.g. the same verticle instance) then the different executeBlocking are executed *serially*". Use `executeBlocking(Callable, false)` for unordered, parallel execution. — [Vert.x 5.2.3 core docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
  - Doc inconsistency: the prose says 10 seconds, but `DEFAULT_MAX_WORKER_EXECUTE_TIME` is 60 s. Not tested.
- 5.2.3 signatures (javap): `<T> Future<T> executeBlocking(Callable<T>)` and `<T> Future<T> executeBlocking(Callable<T>, boolean)`. `HttpServer.listen()`, `listen(int)`, `listen(int,String)` and `listen(SocketAddress)` all return `Future<HttpServer>`; there is no `Handler<AsyncResult>` overload. Compiling the Vert.x 4-style `server.listen(8080, ar -> ...)` fails with `error: incompatible types: String is not a functional interface`, because the only two-argument overload is `listen(int, String)`. — (javap and local compile against vertx-core-5.2.3)
- Migration guide, futures: "Vert.x 4 extended the 3.x callback asynchronous model to a future/callback hybrid model... Vert.x 5 only retains the future model and thus the callback model is gone". — [vertx-5-migration-guide: embracing_the_future_model.adoc](https://github.com/vert-x3/vertx-5-migration-guide/blob/main/asciidoc/modules/embracing_the_future_model.adoc) (via git clone)
- Migration guide, core: "Removal of execute blocking methods with a handler of promise". `vertx.executeBlocking(promise -> promise.complete("result"))` becomes `vertx.executeBlocking(() -> "result")`. `DeploymentOptions#setWorker` is removed; use `setThreadingModel(ThreadingModel.WORKER)`. "Since Vert.x 5 worker deployment uses a single event-loop for all worker verticles instead of an event-loop per worker instance." — [vertx-5-migration-guide: vertx_core.adoc](https://github.com/vert-x3/vertx-5-migration-guide/blob/main/asciidoc/modules/vertx_core.adoc) (via git clone)
- `ThreadingModel` constants [5.2.3]: `EVENT_LOOP`, `WORKER`, `VIRTUAL_THREAD`, `EXTERNAL`. `io.vertx.core.VerticleBase` (start/stop return `Future<?>`) exists alongside `AbstractVerticle`. — (javap, local)
- Observed thread placement (local run):
  ```
  [EVENT_LOOP verticle] start() on Thread[#25,vert.x-eventloop-thread-0,5,main] isEventLoopContext=true isWorkerContext=false
  [WORKER verticle] start() on Thread[#27,vert.x-worker-thread-0,5,main] isEventLoopContext=false isWorkerContext=true
  [VIRTUAL_THREAD verticle] start() on VirtualThread[#28,vert.x-virtual-thread-0]/runnable@ForkJoinPool-1-worker-1 isEventLoopContext=false isWorkerContext=false
  [executeBlocking] callable ran on vert.x-worker-thread-1; onSuccess runs on vert.x-eventloop-thread-1
  ```
- **The "blocking JDBC in a handler" experiment** (local run). HTTP server on one event loop; 4 concurrent requests, each doing a 500 ms `Thread.sleep` that stands in for JDBC:
  ```
  block-on-event-loop        4 requests x 500 ms -> 2814 ms total, ran on [vert.x-eventloop-thread-0]
  executeBlocking-ordered    4 requests x 500 ms -> 2043 ms total, ran on [vert.x-worker-thread-0]
  executeBlocking-unordered  4 requests x 500 ms ->  576 ms total, ran on [vert.x-worker-thread-0, vert.x-worker-thread-1, vert.x-worker-thread-2, vert.x-worker-thread-3]
  ```
  Default `executeBlocking` is **ordered per context**. All requests to one server share its context, so they were still serialized: 2 s. Only `ordered=false` parallelized them.

### Inferences
- The ordered-by-default `executeBlocking` is a strong "gotcha" for experienced engineers. Moving work off the loop alone isn't enough. Calls from one context queue behind each other unless you pass `false`, use a worker verticle with multiple instances, or use a reactive client.
- For a lesson about Vert.x 5's API, show the javap signatures plus the compile error. That is concrete evidence the callback API is gone.

### Gaps
- vertx.io (rendered docs, migration guide site) was unreachable. Repository sources were used instead.
- I did not test `setMaxEventLoopExecuteTime` customisation or a `blockedThreadCheckInterval` override, though both setters exist per the docs.

---

## Q6. Quarkus REST (formerly RESTEasy Reactive): event loop vs worker threads, @Blocking/@NonBlocking, @RunOnVirtualThread, blocking the IO thread

### Takeaway
[Quarkus 3.x, checked at tag 3.40.1] Quarkus REST picks the thread from the method signature:
- Methods returning `Uni`, `Multi`, `CompletionStage`, `Publisher`, or Kotlin `suspend` functions run on the **IO (event-loop) thread**.
- Everything else runs on a **worker thread**.
- `@Blocking` / `@NonBlocking` override this at method, class or `Application` level.
- `@RunOnVirtualThread` runs the method on a new virtual thread.

Quarkus's Vert.x is configured with event loops = #CPUs (min 2, memory-capped), `max-event-loop-execute-time` = 2 s and `warning-exception-time` = 2 s. Blocking an IO thread therefore produces the Vert.x warning above, with a stack trace already at 2 s. Some Quarkus APIs throw `BlockingOperationNotAllowedException` outright when called on an IO thread.

### Cited Findings
- "Quarkus REST is implemented using two main thread types: Event-loop threads: which are responsible, among other things, for reading bytes from the HTTP request and writing bytes back to the HTTP response; Worker threads: they are pooled and can be used to offload long-running operations."
- "By default, the thread Quarkus REST will run endpoint methods on depends on the signature of the method. If a method returns one of the following types then it is considered non-blocking, and will be run on the IO thread by default: `io.smallrye.mutiny.Uni`, `io.smallrye.mutiny.Multi`, `java.util.concurrent.CompletionStage`, `org.reactivestreams.Publisher`, Kotlin `suspended` methods". "If you are writing blocking code, your methods will usually return the result directly, and these will be run on a worker thread."
- Override with `@Blocking` / `@NonBlocking` "at the method, class or `jakarta.ws.rs.core.Application` level". Example: `@Blocking @GET public Uni<String> blockingHello() { Thread.sleep(1000); ... }` runs on a worker even though it returns `Uni`.

  — [rest.adoc @ 3.40.1, "Execution model, blocking, non-blocking"](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc)
- Filters follow the endpoint. Under `@Blocking` they run on the worker. Under `@NonBlocking`, "(or is not annotated at all)", they run on the event loop. `@ServerRequestFilter(nonBlocking=true)` forces the event loop. — [rest.adoc (main)](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/rest.adoc)
- **Conflict, `@Transactional`:**
  - The 3.40.1-tagged `rest.adoc` says: "If a method or class is annotated with `jakarta.transaction.Transactional` then it will also be treated as a blocking method. This is because JTA is a blocking technology". — [rest.adoc @ 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc)
  - The **main** branch says the opposite: "it is no longer automatically treated as a blocking method (since Quarkus 3.35). The default behavior is now based on the return type... If you have a blocking method that returns a `Uni` and uses JTA transactions... you must add an explicit `@Blocking` annotation." — [rest.adoc (main)](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/rest.adoc)
  - The two texts disagree, and the "3.35" version claim is **unresolved**: I did not locate the code that applies the rule. Lesson writers should state the rule for the exact Quarkus version the course pins, and recommend an explicit `@Blocking` on JTA endpoints that return `Uni` either way.
- At 3.40.1, Narayana's `TransactionalInterceptorBase.checkBlockingAllowed()` throws `BlockingOperationNotAllowedException("@Transactional cannot start a JTA transaction within a reactive pipeline. If the annotated method is intended to be blocking, ensure it is executed on a worker thread, for example by annotating it with @Blocking. If the annotated method is intended to be reactive, consider using Hibernate Reactive, which supports @Transactional in a reactive context.")` when `!BlockingOperationControl.isBlockingAllowed()`. — [TransactionalInterceptorBase.java @ 3.40.1](https://github.com/quarkusio/quarkus/blob/3.40.1/extensions/narayana-jta/runtime/src/main/java/io/quarkus/narayana/jta/runtime/interceptor/TransactionalInterceptorBase.java) (via sparse git clone)
- Reading the request body as a blocking stream on the IO thread throws `new BlockingOperationNotAllowedException("Attempting a blocking read on io thread")` (`VertxInputStream`). `BlockingOperationNotAllowedException extends IllegalStateException`. `BlockingOperationControl.isBlockingAllowed()` consults registered `IOThreadDetector`s. — [VertxInputStream.java @ 3.40.1](https://github.com/quarkusio/quarkus/blob/3.40.1/extensions/vertx-http/runtime/src/main/java/io/quarkus/vertx/http/runtime/VertxInputStream.java) (via git); [BlockingOperationNotAllowedException.java @ 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/core/runtime/src/main/java/io/quarkus/runtime/BlockingOperationNotAllowedException.java); [BlockingOperationControl.java @ 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/core/runtime/src/main/java/io/quarkus/runtime/BlockingOperationControl.java)
- Quarkus Vert.x config [3.40.1] (`VertxConfiguration`):
  - `eventLoopsPoolSize`: "By default, it matches the number of CPUs detected on the system."
  - `maxEventLoopExecuteTime` `@WithDefault("2")` (seconds): "The maximum amount of time the event loop can be blocked."
  - `warningExceptionTime` `@WithDefault("2")`
  - `workerPoolSize` defaults to `${quarkus.thread-pool.max-threads:20}` and is deprecated in favour of `quarkus.thread-pool.max-threads`
  - `maxWorkerExecuteTime` 60 s
  - `internalBlockingPoolSize` 20

  — [VertxConfiguration.java @ 3.40.1](https://github.com/quarkusio/quarkus/blob/3.40.1/extensions/vertx/runtime/src/main/java/io/quarkus/vertx/core/runtime/config/VertxConfiguration.java) (via git)
- `VertxCoreRecorder.calculateDefaultIOThreads()` returns `Math.max(2, Math.min(maxMemoryMB / 10, availableProcessors))`. Its comment reads: "We used to recommend a default of twice the number of cores, but more recent developments seem to suggest matching the number of cores 1:1 being a more reasonable default. It also saves memory." The recorder applies `setMaxEventLoopExecuteTime(...)` and `setWarningExceptionTime(...)` from that config. Plain Vert.x defaults to 2× cores; Quarkus to 1×. — [VertxCoreRecorder.java @ 3.40.1](https://github.com/quarkusio/quarkus/blob/3.40.1/extensions/vertx/runtime/src/main/java/io/quarkus/vertx/core/runtime/VertxCoreRecorder.java) (via git)
- Reactive architecture guide: "the HTTP request is always received on an I/O thread. Then, the extension dispatching that request to your code decides whether to call it on the I/O thread, avoiding thread switches, or on a worker thread. This decision depends on the extension." The engine is "powered by Eclipse Vert.x and Netty". — [quarkus-reactive-architecture.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc)
- `@RunOnVirtualThread`: "instructs Quarkus to invoke the annotated method on a **new** virtual thread instead of the current one... the fundamental idea... is to offload the execution of an endpoint handler on a new virtual thread instead of running it on an event-loop or worker thread". The guide's comparison table:
  - `Fortune blocking()` is synchronous on a worker thread. Pro: simple code. Con: "Use worker thread (limit concurrency)".
  - `Uni<Fortune> reactive()` is reactive on the event loop. Pro: "High concurrency and low resource usage". Con: "More complex code".
  - `@RunOnVirtualThread Fortune vt()` is synchronous on a virtual thread. Pro: simple code. Con: "Risk of pinning, monopolization and under-efficient object pooling".

  "Note that all three models can be used in a single application." — [virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc)
- Virtual threads "are useful for I/O-bound workloads only". A CPU-bound virtual thread "monopolizes the carrier thread". On the pooling case, "Extremely popular libraries like Jackson and Netty assume that the application uses a limited number of threads, which are recycled". Use `uni.await().atMost(...)` / Mutiny `andAwait()` on virtual threads to block without pinning. — [virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc)

### Inferences
- What happens when you block the IO thread in Quarkus (inferred from the wiring above; not run in a Quarkus app):
  - A `Uni`-returning or `@NonBlocking` endpoint that calls `Thread.sleep` or JDBC stalls every other connection on that event loop.
  - After 2 s the logs show `Thread vert.x-eventloop-thread-N has been blocked for … ms, time limit is 2000 ms`, already with a `VertxException: Thread blocked` stack trace, because Quarkus's `warningExceptionTime` is 2 s.
  - Guarded APIs fail fast with `BlockingOperationNotAllowedException`: blocking body reads, JTA `@Transactional`.
- A senior Quarkus engineer's mental model: "return type picks the thread". A `Uni` return means you have promised not to block.

### Gaps
- No Quarkus app was built or run, so the exact Quarkus log line formatting (JBoss Log Manager) was not captured.
- The default of `quarkus.thread-pool.max-threads` was not verified (only the `:20` fallback in the Vert.x config expression).
- Whether `@Transactional` implies `@Blocking` in 3.35–3.40 is unresolved (see the conflict above).

---

## Q7. Zero-copy (transferTo/sendfile, FileRegion, composite buffers) and epoll vs io_uring

### Takeaway
On Linux, `FileChannel.transferTo` to a socket becomes `sendfile(2)`: one syscall moved 64 MiB here, against thousands of `read`/`write` pairs. Netty's `DefaultFileRegion` uses `FileChannel.transferTo` on NIO and native `sendfile` on epoll. On io_uring no `sendfile` syscalls appear; the work goes through `io_uring_enter`, and 4.2 source mentions splicing for `DefaultFileRegion`. Composite buffers give "zero-copy" in user space: they combine buffers without copying bytes.

### Cited Findings
- JDK, 64 MiB file to a loopback socket, `strace -f -c` (local run, JDK 21):
  ```
  zerocopy (FileChannel.transferTo): transferTo calls=1 ; 64 MiB in 95 ms
      sendfile 1 call ; read 300 ; pread64 155 ; write 14      (reads are the receiver + JVM)
  copy (read into 64 KiB heap buffer, write to socket): 64 MiB in 123 ms
      read 2119 ; write 1037 ; pread64 156                      (no sendfile)
  ```
  Timings are a single run and not a benchmark. The syscall shape is the point.
- `DefaultFileRegion.transferTo(WritableByteChannel target, long position)` calls `file.transferTo(this.position + position, count, target)`. — [netty-transport-4.2.20.Final-sources.jar, DefaultFileRegion.java](https://repo.maven.apache.org/maven2/io/netty/netty-transport/4.2.20.Final/)
- Netty 4.2.20, sending a 32 MiB `DefaultFileRegion` to one client, `strace -f -c` (local run):
  ```
  nio:     client received 33554432 bytes in 99 ms   | sendfile 103 calls, 10 errors (EAGAIN on full non-blocking socket)
  epoll:   client received 33554432 bytes in 86 ms   | sendfile 53 calls, 11 errors
  iouring: client received 33554432 bytes in 159 ms  | io_uring_enter 2061, io_uring_setup 9, no sendfile
  ```
  The sendfile "errors" are EAGAIN on a full non-blocking socket. Netty then waits for writability and resumes: the same partial-write logic as Q2. (local run)
- 4.2.20 includes "Use a long file offset when splicing a DefaultFileRegion with io_uring (#18018)". This confirms io_uring serves FileRegion by splicing. — [netty/netty commit a20f453](https://github.com/netty/netty/commit/a20f453) (via git)
- Composite buffers and slices share memory; see the Q4 local-run output (`HDR:Payload`).
- **UNVERIFIED (not checked in source):** `FileRegion` can't be used through `SslHandler` (TLS encrypts in user space); use `ChunkedFile` / `ChunkedWriteHandler` instead.

### Inferences
- epoll vs io_uring, as a teaching contrast:
  - epoll is readiness-based ("tell me when I can read; then I call read"), which is Kegel strategy 1 or 2.
  - io_uring is completion-based ("here is a read; tell me when it's done") with shared submission and completion rings, which is strategy 3.
  - In this local run io_uring was slower than epoll for one bulk file send (159 vs 86 ms, single sample). Don't promise "io_uring is faster". Netty treats it as first-class but still active work (several io_uring fixes landed in Oct–Nov 2026).

### Gaps
- No proper benchmark comparing epoll and io_uring throughput or latency. A single-sample timing is all I have.
- io_uring kernel-version requirements per feature are unverified.

---

## Q8. How virtual threads change the trade-off

### Takeaway
Virtual threads make thread-per-request cheap again for **I/O-bound** code. Each blocking socket read parks the virtual thread on the JDK poller instead of holding an OS thread (2,000 blocked readers ran on 4 carrier threads plus 1–2 poller threads). They don't remove event loops:
- the JDK poller itself is an epoll loop;
- Quarkus and Vert.x still receive every request on a Netty event loop;
- pinning (native frames; `synchronized` before JDK 24), CPU monopolization and thread-assuming pools (Netty, Jackson) remain trade-offs.

### Cited Findings
- 2,000 virtual threads blocked on socket reads used 15 platform threads total (4 FJP carriers, 1 Read-Poller, 1 Write-Poller, 2 Updaters, JVM threads). They all completed 112 ms after data arrived. (local run, JDK 21; see Q3)
- Quarkus: when the virtual thread "attempts to use blocking I/O, the JVM *transforms* this call into a non-blocking one, unmounts the virtual thread, and mounts another virtual thread on the carrier thread... the virtual thread may not be re-mounted on the same carrier thread." — [virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc)
- Pinning and limits, from Quarkus: on Java 21–23, blocking inside `synchronized` pins. On Java 24+, `synchronized` no longer pins (JEP 491), but native code can. The `pgjdbc` driver before 42.6.0 pins frequently on Java 21–23. — [virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc)
- Netty 4.2's adaptive allocator "was also designed from the start to work well with virtual threads". — [Netty 4.2 Migration Guide](https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md)
- Vert.x 5 has `ThreadingModel.VIRTUAL_THREAD` verticles. Observed: they run on `VirtualThread[#28,vert.x-virtual-thread-0]/runnable@ForkJoinPool-1-worker-1`. (local run)
- From JDK 22 onward on Linux, the JDK's poller threads are themselves virtual threads (`VTHREAD_POLLERS`), "to integrate polling with virtual thread scheduling". — [Poller.java (jdk25u)](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java)

### Inferences
- Decision rule for the course:
  - Use **event loop + reactive** when you need maximal concurrency per byte of memory and the whole stack is async: reactive SQL clients, Mutiny.
  - Use **virtual threads** when the code is naturally blocking (JDBC, legacy SDKs) and I/O-bound.
  - Use **worker pool** when you need bounded concurrency, e.g. protecting a 20-connection DB pool. Virtual threads don't bound concurrency; a semaphore or the pool itself must.
- Even with virtual threads, never block a *Netty/Vert.x event-loop* thread. `@RunOnVirtualThread` works by moving the work *off* the event loop.

### Gaps
- No JDK 25 run, so post-JDK-22 scheduling behaviour (virtual sub-pollers) is from source only.

---

## Verified URLs

Fetched directly (curl or WebFetch, HTTP 200, content read):
- https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk22u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk22u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk23u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk24u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk24u/master/src/hotspot/share/services/diagnosticCommand.hpp
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/PollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/macosx/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/EPollSelectorImpl.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/hotspot/share/services/diagnosticCommand.hpp
- https://raw.githubusercontent.com/openjdk/jdk25u/master/make/conf/version-numbers.conf
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/SelectionKey.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/WritableByteChannel.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/ReadableByteChannel.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/X-Buffer.java.template
- https://raw.githubusercontent.com/openjdk/jdk26u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk27u/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk27u/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk27u/master/make/conf/version-numbers.conf
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/Poller.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/DefaultPollerProvider.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/EPollSelectorImpl.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/EPollPoller.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/linux/classes/sun/nio/ch/DefaultSelectorProvider.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/macosx/classes/sun/nio/ch/DefaultSelectorProvider.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/IOUtil.java
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/NioSocketImpl.java
- https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf
- https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md
- https://raw.githubusercontent.com/wiki/netty/netty/Reference-counted-objects.md
- https://raw.githubusercontent.com/netty/netty/4.2/common/src/main/java/io/netty/util/ResourceLeakDetector.java
- https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/MultiThreadIoEventLoopGroup.java
- https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/nio/NioIoHandler.java
- https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/nio/NioEventLoopGroup.java
- https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc
- https://raw.githubusercontent.com/vert-x3/vertx-5-migration-guide/main/README.md
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/rest.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/core/runtime/src/main/java/io/quarkus/runtime/BlockingOperationControl.java
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/core/runtime/src/main/java/io/quarkus/runtime/BlockingOperationNotAllowedException.java

Read via `git clone` into the scratchpad, not the course repo. The commit and blob URLs below are the canonical GitHub locations of what I read; I did not load the HTML pages themselves:
- https://github.com/vert-x3/vertx-5-migration-guide (`asciidoc/modules/embracing_the_future_model.adoc`, `asciidoc/modules/vertx_core.adoc`)
- https://github.com/netty/netty.wiki (`Netty-4.2-Migration-Guide.md`, `Reference-counted-objects.md`)
- https://github.com/netty/netty, branch 4.2 history since 2024-01-01: commits `d64340b`, `50ffe5b`, `06518dc`, `a20f453`, `77077ff`, `09e64d2` (4.2.0.Final), `4fb6a5f` (4.2.20.Final)
- https://github.com/openjdk/jdk, master history since 2023-05-01: commits `c099cf53` (8318422), `78b80150` (8338383 / JEP 491), `5c8cb2ed` (8337199), `cd5256d5` (8374170), `dfebf8c5` (8394217)
- https://github.com/quarkusio/quarkus at tag 3.40.1, sparse: `extensions/vertx/runtime/.../VertxConfiguration.java`, `.../VertxCoreRecorder.java`, `extensions/vertx-http/runtime/.../VertxInputStream.java`, `extensions/narayana-jta/runtime/.../TransactionalInterceptorBase.java`
- Tag listings via `git ls-remote --tags` for netty/netty, eclipse-vertx/vert.x, quarkusio/quarkus

Read from Maven Central artifacts (downloaded with `mvn dependency:copy-dependencies`, inspected with javap/unzip):
- https://repo.maven.apache.org/maven2/io/netty/netty-all/4.2.20.Final/ and per-module jars plus `-sources.jar`: netty-transport, netty-common, netty-buffer, netty-transport-classes-io_uring
- https://repo.maven.apache.org/maven2/io/vertx/vertx-core/5.2.3/ (jar and `-sources.jar`)
- https://repo.maven.apache.org/maven2/io/vertx/vertx-dependencies/5.2.3/vertx-dependencies-5.2.3.pom
- The GCS mirror https://maven-central.storage-download.googleapis.com/maven2/io/netty/netty-all/4.2.20.Final/netty-all-4.2.20.Final.pom also returned 200.

Attempted but unreachable (not used as sources): http://www.kegel.com/c10k.html, https://openjdk.org/jeps/491, https://netty.io, https://vertx.io, https://quarkus.io, https://docs.oracle.com/en/java/javase/25/

---

## Teaching notes

### Misconceptions, each with evidence to show
1. **"Non-blocking means faster."** Non-blocking improves *concurrency per thread*, not per-request latency.
   - Vert.x's own argument is about scalability ("a blocking approach just doesn't scale"), not speed ([Vert.x docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)).
   - In the Vert.x JDBC experiment each request still took ≥ 500 ms. Only the overlap changed: 2,814 ms → 576 ms for 4 requests.
   - io_uring was slower than epoll in the single FileRegion run (159 vs 86 ms).

   (local runs)
2. **"The event loop is a thread pool."** An `EventLoop` is one thread. A group is a set of single-threaded loops, and each channel is pinned to one of them for life. Observed: connections land on `-4-1`, `-4-2`, `-4-1`, with `inEventLoop=true` inside handlers. One sleeping handler delayed an unrelated client by 1,060 ms because both channels shared the loop. Vert.x: "any particular handler will never be executed concurrently". (local runs; [Vert.x docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc))
3. **"You can call a blocking JDBC driver from a Vert.x handler."** The golden rule lists "a long lived database operation" as blocking. The demo serialized 4 requests to 2.8 s. The non-obvious second half: default `executeBlocking` is **ordered per context**, so it still took 2.0 s. Only `executeBlocking(callable, false)` (576 ms), worker verticles or reactive clients fix it. In Quarkus, a `Uni`-returning endpoint runs on the IO thread, so a JDBC call inside it blocks the loop. JTA there throws `BlockingOperationNotAllowedException`. (local run; [rest.adoc @3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc); [TransactionalInterceptorBase @3.40.1](https://github.com/quarkusio/quarkus/blob/3.40.1/extensions/narayana-jta/runtime/src/main/java/io/quarkus/narayana/jta/runtime/interceptor/TransactionalInterceptorBase.java))
4. **"Direct buffers are always better."** The JDK Javadoc says they have "higher allocation and deallocation costs" and recommends them "primarily for large, long-lived buffers". Their benefit is that native IO skips the temporary-direct-buffer copy that `IOUtil` performs for heap buffers. The real-world answer is to pool them, which Netty's allocators do (default `AdaptiveByteBufAllocator` → direct `AdaptiveByteBuf`). ([X-Buffer.java.template](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/X-Buffer.java.template); [IOUtil.java](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/sun/nio/ch/IOUtil.java); local run). Don't use the crude allocation timing as evidence; it was noisy and contradictory across rounds.
5. **"Virtual threads make event loops obsolete."** The JDK implements virtual-thread socket blocking *with* an event loop: the `sun.nio.ch.Poller` sits in `EPoll.wait`, and the parked frames are visible in the jcmd stack. On JDK 22+ Linux those pollers are themselves virtual threads. Quarkus still accepts every request on a Vert.x/Netty IO thread and lists virtual-thread cons (pinning, monopolization, pooling). (local run; [Poller.java jdk25u](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/sun/nio/ch/Poller.java); [virtual-threads.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc))
6. Bonus for Netty 4.1 veterans: **"Add the handler with an EventExecutorGroup to offload."** This is deprecated in 4.2 (commit d64340b). Dispatch manually to an application executor and write back with `ctx.writeAndFlush`. The measured lag probe went from 1,070 ms to 0 ms.

### Analogies
- **Event loop = a single waiter covering many tables.** They take an order (read), hand it to the kitchen (async IO or worker pool), and move on. A waiter who stands at one table waiting for the kitchen (a blocking call) leaves every other table unserved. The Vert.x "blocked thread" warning is the manager noticing.
- **ByteBuffer = a notepad with a pencil (position) and a "written up to here" line (limit).** `flip()` = "stop writing, go back to the top and read up to the line". `compact()` = "erase what you've read and slide the rest to the top".
- **Level- vs edge-triggered:** level = the doorbell rings for as long as someone stands at the door (`OP_WRITE` on a writable socket rings forever, hence the spin). Edge = it rings once when someone arrives.
- **Virtual-thread blocking read = a coat check.** The virtual thread hands its ticket (fd) to the poller and leaves the counter (carrier). The poller calls it back when the coat (data) arrives.

### Demos (all ran; outputs recorded above)
- `BufferDemo`: position/limit/capacity through put → flip → get → compact → flip; the forgot-flip bug. (Q2)
- `NioEcho`: Selector echo with partial-write handling (8 MiB echoed; partial writes counted). OP_WRITE busy-spin: 0 vs 94,243 wakeups in 300 ms. strace shows `epoll_wait`. (Q2)
- `VThreadPoller`: 2,000 virtual threads blocked on reads; platform-thread census; jcmd stack through `Poller.pollIndirect`; `-Djdk.readPollers=4`. On JDK 25, add `jcmd <pid> Thread.vthread_pollers`. (Q3)
- `Netty42Demo echo|transports`: NIO, epoll and io_uring echo with `MultiThreadIoEventLoopGroup`; thread names. (Q4)
- `Netty42Demo blocking` and `NettyDispatch`: the latency impact of blocking, and the 4.2 manual-dispatch fix with an event-loop lag probe. (Q4)
- `Netty42Demo embedded|buffers|leak`: EmbeddedChannel fragments; ByteBuf refCnt; composite/slice; PARANOID leak report and listener. (Q4)
- `VertxDemo sleep|models|jdbc|defaults`: exact blocked-thread warnings; threading models; the ordered/unordered `executeBlocking` gotcha. (Q5)
- `ZeroCopy` and `NettyFileRegion` under `strace -c`: sendfile vs read/write; FileRegion on nio, epoll and io_uring. (Q7)
- `-Xlint:deprecation` compile showing `NioEventLoopGroup` and `addLast(EventExecutorGroup, ...)` deprecations, and the Vert.x 5 callback-`listen` compile error. (Q4, Q5)

Practical notes for lab authors, from running these:
- With a proxy-configured environment, `JAVA_TOOL_OPTIONS` prints `Picked up JAVA_TOOL_OPTIONS:` noise to stderr.
- In the Vert.x demo I had to use `java.net.http.HttpClient` with `.proxy(HttpClient.Builder.NO_PROXY)` and fully qualified names, since `io.vertx.core.http.HttpClient` clashes with it.
- `io.vertx.core.Future` clashes with `java.util.concurrent.Future` on wildcard imports.

### Lab exercises (JUnit, localhost, ephemeral ports, short timeouts)
All designs below were exercised by the demos above; expected values are what I observed. Use `@Timeout(5)` on everything. Bind `127.0.0.1:0` and read the port back. Never sleep for correctness; use latches and futures with timeouts.

1. **NIO echo server that survives partial reads and writes.**
   - Student implements the select loop as an `AutoCloseable` that exposes `port()`.
   - Tests:
     - (a) Echo 1–8 MiB of random bytes with client `SO_RCVBUF=4096`, writing and reading concurrently. Assert byte-for-byte equality. Observed: 8 MiB identical in ~150 ms.
     - (b) A framed variant (newline- or length-prefixed). The client sends one message in 3 writes with 20–50 ms gaps. Assert exactly one reply, sent only after the last fragment.
     - (c) Idle-spin check: after the echo, count `select()` returns over 300 ms on an idle connection, via a test hook or by measuring the loop's CPU or iteration counter. Assert < 10. Observed: 0 when correct, ~25k–94k when `OP_WRITE` is left armed.
     - (d) Half-close: the client calls `shutdownOutput()`. The server must flush pending bytes and then close, so the client sees EOF after the full echo.
2. **Netty pipeline with EmbeddedChannel.**
   - Student writes the decoder (or uses `LineBasedFrameDecoder`) plus a business handler.
   - Tests:
     - Fragments `"hel"`, `"lo\nwor"`, `"ld\n"` give outbound `[]`, `["HELLO\n"]`, `["WORLD\n"]`.
     - An oversized line gives `TooLongFrameException` with message `frame length (100) exceeds the allowed maximum (64)`.
     - `finish()` returns `false` when nothing is left over.
   - Release every outbound `ByteBuf` in the test.
3. **Detect and fix a handler that blocks the event loop.**
   - Given: a server on `new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())` whose handler calls `Thread.sleep(1000)` (stand-in for JDBC) on `SLOW`.
   - Detection test: send `SLOW`, then submit a no-op to `group.next()` and measure its delay (the lag probe). It fails with ~1,070 ms when blocking, and passes with < 100 ms once fixed (observed 0 ms). Alternatively, assert a second client's `FAST` round-trip is < 200 ms (observed 1,060 ms broken, 4 ms fixed).
   - Expected fix [4.2]: dispatch to an application executor and `ctx.writeAndFlush` from there. The deprecated `addLast(EventExecutorGroup, …)` also passes the latency test but triggers a deprecation warning; consider failing the build with `-Werror` to steer students. Shut down the executor *after* the channels and event loop group to avoid `RejectedExecutionException` noise.
4. **ByteBuf leak caught by ResourceLeakDetector in PARANOID mode.**
   - Setup: `ResourceLeakDetector.setLevel(PARANOID)` in `@BeforeAll`, or `-Dio.netty.leakDetection.level=paranoid` in the Gradle test task's `jvmArgs`, then `ByteBufUtil.setLeakListener((type, records) -> leaks.add(type))`.
   - Given handler: consumes inbound `ByteBuf` without releasing it.
   - Test:
     1. Push 10 buffers through `EmbeddedChannel`, then `finishAndReleaseAll()`.
     2. Loop up to 20× `{ System.gc(); Thread.sleep(50); ByteBufAllocator.DEFAULT.buffer(8).release(); }`. Detection runs on later allocations, so you must allocate after GC.
     3. Assert `leaks` is non-empty for the buggy handler and empty for the fixed one (`ReferenceCountUtil.release(msg)` or `SimpleChannelInboundHandler`).
   - Observed: 1 leak reported for 10 leaked buffers (de-duplication), log line starting `LEAK: ByteBuf.release() was not called before it's garbage-collected.`
   - GC timing is not fully deterministic, so pair it with a deterministic assertion: keep a reference to the input buffer and assert `refCnt() == 0` after `writeInbound`.
   - Reset the listener and level in `@AfterAll`.
5. Optional Vert.x lab: **Find the blocked event loop.**
   - Capture JUL logger `io.vertx.core.impl.BlockedThreadChecker` with a custom `Handler`.
   - Set `VertxOptions.setMaxEventLoopExecuteTime(200)` + `setMaxEventLoopExecuteTimeUnit(MILLISECONDS)` and `setBlockedThreadCheckInterval(50)` to keep the test short. These setters are documented; the shortened timings themselves are **not run**.
   - Assert a record matching `Thread vert.x-eventloop-thread-\d+ has been blocked for \d+ ms, time limit is 200 ms` appears when the handler sleeps.
   - Then fix it with `executeBlocking(callable, false)` and assert no record appears and 4 concurrent requests finish in < 1.5 × the single-request time. Observed full-size numbers: 2,814 / 2,043 / 576 ms.
