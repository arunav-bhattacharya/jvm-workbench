# Jetty 12, Netty in practice, and Vert.x in depth (state as of 2026-11-07)

These notes extend `nio_event_loops.md` (same folder) for the 8-lesson track. They mostly feed io-03/io-04 (Netty), io-05 (Vert.x) and io-07 (Jetty 12), with some comparison material for io-08. They do not repeat the basics already there: NIO, poller internals, Netty 4.2 API shape, leak-detector levels, the Vert.x blocked-thread checker, Quarkus threading.

Conventions:
- [Jetty 12.1.14], [Netty 4.2.20], [Vert.x 5.2.3] mark version-specific facts.
- **UNVERIFIED** marks anything not checked against a primary source.
- "(local run)" means output I produced on OpenJDK 21.0.12.1, 4 CPUs, Linux 6.18, with `jetty-server 12.1.14`, `netty-all 4.2.20.Final`, `vertx-core 5.2.3`, `vertx-junit5 5.2.3`, JUnit 6.1.3 and AssertJ 3.27.7, all resolved from Maven Central.
- Experiments live in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/proj2/`: a Maven project with `src/main/java/demo/*` and `src/test/java/labs/*`. That is scratch space and may not persist, so key code is reproduced here.
- The only file written in the course repo is this one.

Versions (`git ls-remote --tags`, 2026-11-07):
- Jetty's newest 12.1 tag is `jetty-12.1.15`; the labs pin 12.1.14, one patch behind. The 12.0 line is at `jetty-12.0.41`. — [jetty/jetty.project tags](https://github.com/jetty/jetty.project)
- Tomcat's `11.0.x` branch builds `11.0.28`. That is the in-progress dev version, so the latest released 11.0 is probably 11.0.27 (**UNVERIFIED**). — [tomcat 11.0.x build.properties.default](https://raw.githubusercontent.com/apache/tomcat/11.0.x/build.properties.default)

Sources:
- Jetty documentation and source were read from a sparse `git clone` of tag `jetty-12.1.14` (scratchpad only).
- Vert.x and vertx-junit5 docs were read from GitHub raw at tag `5.2.3`, plus the 5.2.3 source jars.
- Netty facts come from the 4.2.20.Final source jars.
- Tomcat docs come from GitHub raw.
- jetty.org, eclipse.dev, netty.io, vertx.io and tomcat.apache.org were not used; those hosts were blocked in the first round.

---

## Q1. Jetty 12 architecture, threading, virtual threads, async core API, HTTP/2 and HTTP/3, and how it compares

### Takeaway
[Jetty 12.1.14] A `Server` links `Connector`s and a `Handler` tree to one `ThreadPool`. The default pool is `QueuedThreadPool`: min 8, max 200, unbounded queue.

A `ServerConnector`:
- runs **acceptor** threads (default 1) that hand accepted sockets to a `SelectorManager`;
- that manager owns N `ManagedSelector`s (one thread each; default `max(1, min(cpus/2, maxThreads/16))`).

Each selector produces tasks that the **AdaptiveExecutionStrategy** (formerly "Eat What You Kill") consumes, using the task's `InvocationType`:
- `NON_BLOCKING` tasks run on the selector thread itself (Produce-Consume, an event loop);
- `BLOCKING` tasks are either consumed by the producing thread while a *reserved* thread takes over selecting (Execute-Produce-Consume, cache-friendly), or dispatched to the pool (Produce-Execute-Consume).

I confirmed all three paths by stack trace.

Virtual threads come in two forms:
- `QueuedThreadPool.setVirtualThreadsExecutor(...)` sends **blocking** tasks to virtual threads. Selectors, acceptors and non-blocking tasks stay on platform threads, and reserved threads default to 0.
- `VirtualThreadPool` runs everything on virtual threads, with a `Semaphore` cap on concurrent tasks (default 200).

The core API is fully asynchronous: `boolean handle(Request, Response, Callback)` must return `true` and later succeed or fail the `Callback`. Request bodies are a `Content.Source` that you read in chunks; every chunk you read must be released. Servlets live in separate `ee8`/`ee9`/`ee10`/`ee11` environments on top of the core.

### Cited Findings

**Architecture: Server, Connector, Handler, ThreadPool**
- "An `org.eclipse.jetty.server.Server` instance is the central component that links together a collection of `Connector`s and a collection of `Handler`s, with threads from a `ThreadPool` doing the work." — [server/http.adoc @ jetty-12.1.14](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc) (via git)
- "`SelectorManager` manages internally a configurable number of `ManagedSelector`s. Each `ManagedSelector` wraps an instance of `java.nio.channels.Selector`..." Sockets are wrapped in an `EndPoint` (bytes: `SocketChannelEndPoint`, `DatagramChannelEndPoint`) and a `Connection` (protocol parsing: HTTP/1.1, HTTP/2, HTTP/3, WebSocket). These pairs can be chained, e.g. for TLS, and swapped via `EndPoint.upgrade(Connection)`. On the server side, "the component that aggregates a `SelectorManager` with a set of `ConnectionFactory`s is `ServerConnector`". `EndPoint.fillInterested(Callback)` maps to OP_READ, and `EndPoint.write(Callback, ByteBuffer...)` hides OP_WRITE and congestion. — [arch/io.adoc @ jetty-12.1.14](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/io.adoc) (via git)
- Acceptors: "threads (typically only one) that compete to accept TCP socket connections". Pending connections queue at the OS level, sized by `acceptQueueSize`. With 0 acceptors, "the `ServerSocketChannel` will be configured in non-blocking mode, and registered in the `SelectorManager`", which uses fewer threads but "may result in increased latency". QUIC/HTTP/3 connectors have zero acceptors. — [server/http.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc)
- Selectors: "Each selector requires one thread... As a rule of thumb, a single selector can easily manage up to 1000-5000 TCP sockets". REST and messaging workloads with busy sockets may need more selectors. — [server/http.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc)
- Defaults in source [12.1.14]:
  - `AbstractConnector`: `acceptors < 0 → 1`, and logs a warning if acceptors > CPUs.
  - `SelectorManager.defaultSelectors` = `max(1, min(cpus/2, threads/16))` for a sized pool, else `max(1, cpus/2)`.
  - `QueuedThreadPool()` = `this(200)` → `(maxThreads=200, minThreads=min(8, maxThreads))`.
  - `ReservedThreadExecutor.reservedThreads`: a configured value ≥ 0 wins; **0 if the executor uses virtual threads**; otherwise `max(1, ceilToNextPowerOfTwo(min(cpus, maxThreads/8)))`.
  - `VirtualThreadPool()` = `this(200)`.

  — [AbstractConnector.java](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-server/src/main/java/org/eclipse/jetty/server/AbstractConnector.java), [SelectorManager.java](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-io/src/main/java/org/eclipse/jetty/io/SelectorManager.java), [QueuedThreadPool.java](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/QueuedThreadPool.java), [ReservedThreadExecutor.java](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/ReservedThreadExecutor.java), [VirtualThreadPool.java](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/VirtualThreadPool.java) (all via git)
- Observed defaults (local run, `new Server()`, 4 CPUs):
  ```
  connector: acceptors=1 selectors=2
  QueuedThreadPool: min=8 max=200 threads=8 leased=3 reservedThreads(config)=-1 virtualThreadsExecutor=false
  platform threads: qtpN-N=7, qtpN-N-acceptor-N@…-ServerConnector@…{HTTP/1.1, (http/1.1)}{127.0.0.1:N}=1, …
  ```
  With `new QueuedThreadPool(12)`: `selectors=1 leased=2`, matching `min(4/2, 12/16)` → 1. Thread names are `qtp<hash>-<id>`. The acceptor thread's name embeds the connector description.

**Threading: execution strategies and why they matter for caches**
- Produce-Consume (PC): "the thread-per-selector mode which is very CPU core cache efficient, but suffers from the head-of-line blocking... This mode is equivalent to the 'selector loop' or 'event loop' models typical of non-blocking I/O frameworks such as NodeJS, Netty and others."
- Produce-Execute-Consume (PEC): "solves the head-of-line blocking... but... It is not CPU cache efficient, because the data available to the producer thread will likely be consumed by another thread running on a different CPU core... The Executor queue may grow indefinitely... A small latency is added to the processing of every task".
- Execute-Produce-Consume (EPC): "a task is consumed by the same thread that produced it (which is CPU core cache efficient). A different thread will be used to continue production."
- Adaptive: `AdaptiveExecutionStrategy` "is the default Jetty execution strategy". "When all tasks are NON_BLOCKING, AdaptiveExecutionStrategy functions in Produce-Consume mode... When tasks are BLOCKING and no reserved threads are available, ... Produce-Execute-Consume... When tasks are BLOCKING and reserved threads are available, it functions in Execute-Produce-Consume mode". Reserved-thread availability is asked through `TryExecutor`.

  — [arch/threads.adoc @ jetty-12.1.14](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc) (via git)
- Source Javadoc names a fourth sub-strategy, **ProduceInvokeConsume (PIC)**, for `InvocationType.EITHER` tasks: they are run via `Invocable.invokeNonBlocking`. Selection order: PC if the task is NON_BLOCKING; EPC if a pending producer is available via `tryExecute`; PIC for EITHER; otherwise PEC. Also: "This strategy was previously named EatWhatYouKill (EWYK) because its preference for a producer to directly consume the tasks that it produces is similar to a hunting proverb that says that a hunter should eat (i.e. consume) what they kill (i.e. produced)." Strategies chain: a selector's strategy produces connection tasks, which can run their own strategy for HTTP/2 streams. — [AdaptiveExecutionStrategy.java @ jetty-12.1.14](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/strategy/AdaptiveExecutionStrategy.java) (via git)
- **Observed** (local run, `JettyStack`). Stack frames below the handler on the second request of a connection, filtered to Jetty and JDK frames:
  ```
  qtp/blocking           -> qtp…-25 :: HttpChannelState$HandlerInvoker.run <- HttpConnection.onFillable <- AdaptiveExecutionStrategy.runTask <- AdaptiveExecutionStrategy.epcRunTask <- …consumeTask <- …tryProduce <- …produce <- QueuedThreadPool.runJob <- QueuedThreadPool$Runner.run
  qtp/nonblocking        -> qtp…-36 :: HttpChannelState$HandlerInvoker.run <- HttpConnection.onFillable <- AdaptiveExecutionStrategy.runTask <- AdaptiveExecutionStrategy.pcRunTask  <- …consumeTask <- …tryProduce <- …produce <- QueuedThreadPool.runJob <- …
  qtp-reserved0/blocking -> qtp…-49 :: HttpChannelState$HandlerInvoker.run <- HttpConnection.onFillable <- QueuedThreadPool.runJob <- QueuedThreadPool$Runner.run      (PEC: dispatched)
  qtp+vt/blocking        -> jetty-vt-1 :: HttpChannelState$HandlerInvoker.run <- HttpConnection.onFillable <- ThreadPerTaskExecutor$TaskRunner.run <- VirtualThread.run (PEC to a virtual thread)
  ```
  The default blocking handler ran in **EPC** on the selector thread, which handed off production. A `Handler.Abstract.NonBlocking` ran in **PC**, directly in the selector's produce loop. `setReservedThreads(0)` forced **PEC**.
- Handler invocation types: "A Handler may be declared as non-blocking (by extending `Handler.Abstract.NonBlocking`) or as blocking (by extending `Handler.Abstract`)... When the Handler tree is non-blocking, Jetty may use the Produce-Consume mode... avoiding a thread hand-off, and saving the cost of being scheduled on a different CPU with cold caches." Warning: if a NonBlocking handler's code blocks, "you risk a server lock-up". Containers combine children's types (`Invocable.combine`): any BLOCKING child makes the container BLOCKING, and dynamic containers are always blocking. — [server/http.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc); [server/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/threads.adoc)
- `Request.demand(Runnable)`: a plain lambda is assumed BLOCKING. Pass an `Invocable.Task` to declare its type. — [server/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/threads.adoc)

**QueuedThreadPool rules**
- "IMPORTANT: The thread pool queue must be unbounded." Jetty may need to run internal tasks to make progress, for example HTTP/2 must write in order to read. "If any of the submitted tasks is rejected because the queue is bounded the server may grind to a halt". Limit concurrency with a QoS handler instead.
- Leased threads: each connector leases one thread per acceptor and per selector, and `ReservedThreadExecutor` leases `reservedThreads`. "There must be enough threads for these components, and at least 1 more thread to handle requests." Suggested sizing: `maxThreads = L + H`.
- "a Java platform thread typically allocates 1 MiB of native memory". Shrinking is controlled by `idleTimeout` and `maxEvictCount`.

  — [arch/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc)

**Virtual threads in Jetty 12**
- `QueuedThreadPool.setVirtualThreadsExecutor(Executor)`: "AdaptiveExecutionStrategy makes use of this setting when it determines that a task should be run with the Produce-Execute-Consume mode: rather than submitting the task to QueuedThreadPool to be run in a platform thread, it submits the task to the virtual threads Executor." "Enabling virtual threads in QueuedThreadPool will default the number of reserved threads to zero... which means that virtual threads will always be used for blocking tasks." Caution: Jetty can't verify that the executor really uses virtual threads. — [arch/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc)
- `VirtualThreadPool` "creates only virtual threads (no platform threads)". "Despite the name, VirtualThreadPool does not pool virtual threads, but allows you to impose a limit on the maximum number of concurrent tasks run by virtual threads, using a Semaphore." It "does not queue the tasks submitted to it but rather spawns a virtual thread", which then waits for a permit. It can also track virtual threads for component dumps. — [arch/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc)
- Pinning: "Even when using virtual threads, Jetty uses non-blocking I/O, and dedicates a thread to each `java.nio.channels.Selector`... Up to Java 23, calling `Selector.select()` from a virtual thread *pins* the carrier thread. Since Java 24, calling `Selector.select()` from a virtual thread does *not* pin the carrier thread." On Java 19–23, N selectors pin N carriers. With fewer cores than selectors, "your system will eventually lock up". Keep selectors below the carrier count, or raise `-Djdk.virtualThreadScheduler.parallelism`. — [arch/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc)
- Helper API [12.1.14, javap]: `VirtualThreads.getNamedVirtualThreadsExecutor(String)`, `getDefaultVirtualThreadsExecutor()`, `areSupported()`, `isVirtualThread()`, `executeOnVirtualThread(Runnable)`. (local javap)
- **Observed** (local run, `JettyDemo basics`, one GET each):
  ```
  [default QTP, Handler.Abstract (BLOCKING)]           -> Thread[#29,qtp1684792003-29,5,main] virtual=false
  [default QTP, Handler.Abstract.NonBlocking]          -> Thread[#36,qtp1276709283-36,5,main] virtual=false
  [QTP + setVirtualThreadsExecutor, BLOCKING]          -> VirtualThread[#63,jetty-vt-0]/runnable@ForkJoinPool-1-worker-1 virtual=true
  [QTP + setVirtualThreadsExecutor, NonBlocking]       -> Thread[#74,qtp1813666644-74,5,main] virtual=false   <- non-blocking stays on the platform thread
  [VirtualThreadPool as server ThreadPool]             -> VirtualThread[#84,vtp-1]/runnable@ForkJoinPool-1-worker-2 virtual=true
     platform threads then: ForkJoinPool-N-worker-N=4, jetty-virtual-thread-pool-keepalive=1, (no qtp threads)
  ```
- **Effect on blocking load** (local run, `JettyDemo load`, 40 concurrent GETs, handler sleeps 500 ms; two runs):
  ```
  QueuedThreadPool(max=12), platform threads   : 2766 / 2647 ms, 10 distinct threads served requests
  QueuedThreadPool(max=12)+virtual executor    :  548 /  533 ms, all on virtual threads
  VirtualThreadPool(maxThreads=8 permits)      : 3031 / 3030 ms (a first run gave 3525 ms), all on virtual threads
  ```
  The JUnit version (30 requests × 300 ms, `QueuedThreadPool(12)`) measured 1,380 ms platform vs 334 ms virtual.

**Async core API: Handler, Callback, Content.Source**
- Jetty 11 → 12: `Handler.handle(String target, Request, HttpServletRequest, HttpServletResponse)` became `Handler.handle(Request request, Response response, Callback callback)`. "this is performed by returning `true` from the `Handler.handle(...)` method, which also requires that the `Callback` parameter must be completed, either by succeeding it or failing it. In Jetty 11, the `Handler.handle(...)` method has a blocking semantic, while in Jetty 12 the `Handler.handle(...)` method has an asynchronous semantic... you can return from the `Handler.handle(...)` method *before* the response has been sent". Other replacements: `AbstractHandler` → `Handler.Abstract`; `HandlerCollection`/`HandlerList` → `Handler.Sequence`. Jetty 12 requires Java 17; Jetty 11 required Java 11. — [migration/11-to-12.adoc @ jetty-12.1.14](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/11-to-12.adoc) (via git)
- `Content.Source`: "a non-blocking demand/read model where a read returns a `Content.Chunk`", made of a ByteBuffer, a `last` flag and a failure. Failure chunks are fatal if `last=true`, transient otherwise (e.g. idle timeout). "A Content.Source must be fully consumed... or failed by calling `Content.Source.fail(Throwable)`... otherwise it may leak underlying resources." "IMPORTANT: A `Content.Chunk` returned by a call to `Content.Source.read()` **must** be released, except for `Content.Chunk`s that are failure chunks." Chunks are slices with no copying between layers, and release lets the bottom layer recycle the buffer. A read loop applies no backpressure; reading one chunk at a time with async consumption does. Helpers: `Content.Source.asStringAsync(source, charset)` and `Content.Source.asInputStream(source)`. — [arch/io.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/io.adoc)
- Minimal core handlers (compiled and run against 12.1.14):
  ```java
  class Blocking extends Handler.Abstract {                 // BLOCKING by default
    public boolean handle(Request req, Response res, Callback cb) throws Exception {
      Thread.sleep(500);                                     // stand-in for JDBC
      Content.Sink.write(res, true, "done\n", cb);           // completes cb when written
      return true;                                           // "I handled it"
    } }
  class AsyncEcho extends Handler.Abstract.NonBlocking {     // declares NON_BLOCKING
    public boolean handle(Request req, Response res, Callback cb) {
      Content.Source.asStringAsync(req, UTF_8).whenComplete((body, x) -> {
        if (x != null) { Response.writeError(req, res, cb, x); return; }
        Content.Sink.write(res, true, "body='" + body + "'\n", cb); });
      return true;                                           // returns before the response is written
    } }
  Server s = new Server(pool); ServerConnector c = new ServerConnector(s); c.setHost("127.0.0.1"); c.setPort(0);
  s.addConnector(c); s.setHandler(handler); s.start(); int port = c.getLocalPort();
  ```
  Observed AsyncEcho output: `handle() ran on qtp1424082571-45; body='ping' written from qtp1424082571-45`. The body was already buffered, so the future completed on the same thread. (local run)
- With no SLF4J provider on the classpath, Jetty prints `SLF4J(W): No SLF4J providers were found... Defaulting to no-operation (NOP) logger implementation`. Labs should add `slf4j-simple` (or similar) to `testRuntimeOnly` if they want Jetty logs. (local run)

**Servlet environments ee8/ee9/ee10/ee11**
- "With the introduction of the Jetty Core APIs, modules that in Jetty 11 were implicitly based on the Servlet APIs, in Jetty 12 have been renamed to `{ee8,9,10,11}-<name>.mod`." Modules that keep the old name, e.g. `security.mod`, now use the Core APIs. — [migration/11-to-12.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/11-to-12.adoc)
- "The main theme of Jetty 12.1.x is the implementation of the Jakarta EE 11 specifications, so that now Jetty 12.1.x supports Java EE 8, Jakarta EE 9, Jakarta EE 10 and Jakarta EE 11." EE 11 means Servlet 6.1, Pages 4.0, WebSocket 2.2. Modules available for EE 10 (`ee10-servlet`, ...) now also exist as `ee11-*`. Also new in 12.1:
  - a rewritten deployer with one scanner;
  - pluggable compression (`CompressionHandler` replaces the deprecated `GzipHandler`, with Brotli and Zstandard via native libs);
  - new authenticators.

  The docs attributes set `ee-current: ee11`. — [migration/12.0-to-12.1.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/12.0-to-12.1.adoc); [documentation/jetty/antora.yml](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/antora.yml)
- Jetty Handler API pros, per the docs: "Simple minimalist asynchronous APIs. Very low overhead, only configure the features you use. Faster turnaround to implement new APIs or new standards." Jakarta EE pros: "Standard, well known, APIs." — [server/http.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc)
- **UNVERIFIED** (from memory): ee8 = `javax.servlet` 4.0, ee9 = Servlet 5.0, ee10 = Servlet 6.0. The Java version required by 12.1 was not checked; 12.0 needs Java 17.

**HTTP/2 and HTTP/3, briefly**
- Most apps should use the generic HTTP server library with the HTTP/2 `ConnectionFactory`s. The low-level HTTP/2 and HTTP/3 libraries are for rare use cases. — [server/http2.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http2.adoc); [server/http3.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http3.adoc)
- HTTP/2 data flow control is one reason the pool queue must be unbounded: "the implementation must be able to write in order to progress reads (and must be able to read in order to progress writes)". — [arch/threads.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc)
- HTTP/3 [12.1.14]: "Jetty only implements the HTTP/3 layer in Java; the QUIC implementation is provided by the Quiche native library, that Jetty calls via JNA". It "can only be used on the platforms (OS and CPU) supported by the Quiche native library". It uses `QuicheServerConnector` over a `DatagramChannel`, with zero acceptors and a single selector. Key and certificate must be exported as PEM for Quiche. — [server/http.adoc](https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc)

**Comparison material: Tomcat 11 NIO connector (official docs source)**
- `maxThreads`: "If not specified, this attribute is set to 200". It is ignored when a shared `executor` is set.
- `maxConnections`: "The default value is 8192"; it can be set to -1 for NIO/NIO2.
- `acceptCount` (OS backlog): "The default value is 100".
- Protocols: `Http11NioProtocol` ("non blocking Java NIO connector") and `Http11Nio2Protocol`.
- `useVirtualThreads`: "Use this attribute to enable or disable usage of virtual threads with the internal executor... The default value is false."
- The NIO connector supports sendfile, which takes precedence over compression for static files over 48 KiB.

  — [tomcat 11.0.x webapps/docs/config/http.xml](https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/http.xml)
- Tomcat `Executor`: default `namePrefix` is `tomcat-exec-`, `maxThreads` 200, min spare 25. `org.apache.catalina.core.StandardVirtualThreadExecutor` "uses a new virtual thread to execute each task", with default prefix `tomcat-virt-`. — [tomcat 11.0.x executor.xml](https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/executor.xml)
- **UNVERIFIED** (from memory, not in the fetched text): Tomcat NIO uses an Acceptor thread plus a Poller thread (`http-nio-<port>-Poller`) that dispatches every request to the executor, i.e. always PEC-style.

### Inferences
- Comparison for a backend team:
  - **Netty-based servers** (Vert.x/Quarkus, Reactor Netty) are PC-only. The event loop runs your code, and you must offload blocking work yourself.
  - **Tomcat** always dispatches from poller to worker pool (PEC). Blocking code is safe, but every request pays a thread hop and cold caches.
  - **Jetty 12** chooses per task from the declared `InvocationType`: PC for code that claims to be non-blocking, EPC or PEC for blocking code. Virtual threads are a drop-in for the PEC path.

  Jetty therefore asks you to declare honestly whether your handler blocks. Declaring `NonBlocking` and then blocking reproduces the event-loop failure mode ("server lock-up").
- `VirtualThreadPool(8)` taking about 3.0–3.5 s, not the 2.5 s ideal (40×500 ms / 8), fits the acceptor and selector tasks holding permits for their lifetime (2 of 8 here), plus JDK 21 selector pinning. This is inferred, not measured. Size `VirtualThreadPool.maxThreads` as "concurrent requests + acceptors + selectors", and prefer `QueuedThreadPool` + `setVirtualThreadsExecutor` on JDK 21–23.

### Gaps
- Not run: HTTP/2 or HTTP/3 servers, the ee11 `ServletContextHandler`, `QoSHandler`, `Request.demand`-based streaming reads.
- The Tomcat thread-naming and poller model above is unverified.
- Jetty's own Javadoc site (javadoc.jetty.org) and jetty.org were not reachable. Facts come from the docs sources and code in the repo.

---

## Q2. Netty in practice: codecs, flow control, pooling and leak details

### Takeaway
[Netty 4.2.20] Frame first, then decode:
- `LengthFieldBasedFrameDecoder` (or Line/Delimiter/FixedLength) turns a byte stream into whole frames;
- a `ByteToMessageDecoder` (never `@Sharable`) or `MessageToMessageDecoder` maps frames to objects;
- a `MessageToByteEncoder<T>` writes them back.

Flow control is writability:
- the outbound buffer flips `isWritable()` to false above the high water mark (default 64 KiB) and back to true below the low mark (32 KiB), firing `channelWritabilityChanged` each time;
- to propagate backpressure, stop reading (`setAutoRead(false)`) from whoever feeds an unwritable channel, and resume on writability.

Two traps I reproduced:
- calling `close()` straight after the last `flush()` drops bytes still in the outbound buffer;
- writability events re-enter your handler during `flush()`.

The default allocator is `adaptive` (`io.netty.allocator.type`).

### Cited Findings

**Codecs (4.2.20 source Javadoc):**
- `ByteToMessageDecoder`, on frame detection: "Generally frame detection should be handled earlier in the pipeline by adding a `DelimiterBasedFrameDecoder`, `FixedLengthFrameDecoder`, `LengthFieldBasedFrameDecoder`, or `LineBasedFrameDecoder`." For custom decoders: "If there are not enough bytes for a complete frame, return without modifying the reader index". "One **MUST** use the reader index when using methods like `ByteBuf#getInt(int)`... Use `in.getInt(in.readerIndex())` instead."
- `ByteToMessageDecoder` pitfalls: "subclasses of ByteToMessageDecoder **MUST NOT** annotated with `@Sharable`". "Some methods such as `ByteBuf#readBytes(int)` will cause a memory leak if the returned buffer is not released or added to the out List. Use derived buffers like `ByteBuf#readSlice(int)`".

  — [netty-codec-base-4.2.20.Final-sources.jar, ByteToMessageDecoder.java](https://repo.maven.apache.org/maven2/io/netty/netty-codec-base/4.2.20.Final/)
- Cumulation [4.2.20]: the default `cumulator = MERGE_CUMULATOR` copies into one buffer. `COMPOSITE_CUMULATOR` avoids copies but "may be slower". `discardAfterReads = 16` compacts after 16 reads. `setSingleDecode(boolean)` exists. — [ByteToMessageDecoder.java](https://repo.maven.apache.org/maven2/io/netty/netty-codec-base/4.2.20.Final/)
- `LengthFieldBasedFrameDecoder` "splits the received ByteBufs dynamically by the value of the length field in the message... particularly useful when you decode a binary message which has an integer header field". Parameters: `lengthFieldOffset`, `lengthFieldLength`, `lengthAdjustment`, `initialBytesToStrip`; the Javadoc diagrams each case. — [LengthFieldBasedFrameDecoder.java](https://repo.maven.apache.org/maven2/io/netty/netty-codec-base/4.2.20.Final/)
- `MessageToByteEncoder<I>` extends `ChannelOutboundHandlerAdapter`. Its `preferDirect` constructor flag chooses a direct target buffer. — [MessageToByteEncoder.java](https://repo.maven.apache.org/maven2/io/netty/netty-codec-base/4.2.20.Final/)
- `FlowControlHandler` "ensures that only one message per `read()` is sent downstream". This matters with `AUTO_READ=false`, because decoders "are free to emit as many events as they like for any given input". Javadoc example: `HttpServerCodec` → `FlowControlHandler` → handler. — [netty-handler-4.2.20.Final-sources.jar, FlowControlHandler.java](https://repo.maven.apache.org/maven2/io/netty/netty-handler/4.2.20.Final/)
- **Observed codec run** (local run, `NettyDepth codec`; wire format `[int len][byte type][utf8]`; pipeline `LengthFieldBasedFrameDecoder(1024,0,4,0,4)` → `MsgDecoder extends ByteToMessageDecoder` → `MsgEncoder extends MessageToByteEncoder<Msg>` → handler that upper-cases and increments the type; input fed in arbitrary slices):
  ```
  wire bytes=24 hex=000000060168656c6c6f0000000a076e6574747920342e32
  inbound bytes [ 0, 3) -> replies []                        (half a length field)
  inbound bytes [ 3, 9) -> replies []                        (frame 1 body incomplete)
  inbound bytes [ 9,11) -> replies [Msg[type=2, text=HELLO]] (frame 1 done, frame 2 begun)
  inbound bytes [11,24) -> replies [Msg[type=8, text=NETTY 4.2]]
  length 5000 > max 1024 -> TooLongFrameException: Adjusted frame length exceeds 1024: 5004 - discarded
  finish()=false
  ```
  Run with `-Dio.netty.leakDetection.level=paranoid`: no LEAK reports.

**Flow control:**
- `WriteBufferWaterMark`: `DEFAULT_LOW_WATER_MARK = 32 * 1024`, `DEFAULT_HIGH_WATER_MARK = 64 * 1024`, `WriteBufferWaterMark.DEFAULT`. It is set via `ChannelOption.WRITE_BUFFER_WATER_MARK`. `ChannelOption.AUTO_READ` exists. `Channel.isWritable()` delegates to `ChannelOutboundBuffer.isWritable()`. `bytesBeforeUnwritable()` reports "how many bytes can be written until `isWritable()` returns false". `ChannelInboundHandler.channelWritabilityChanged(ctx)` is the event. — [netty-transport-4.2.20.Final-sources.jar](https://repo.maven.apache.org/maven2/io/netty/netty-transport/4.2.20.Final/) (WriteBufferWaterMark.java, ChannelOption.java, Channel.java, ChannelInboundHandler.java)
- **Observed writability** (local run, `NettyDepth writability`). The server pumps 8 KiB chunks while `isWritable()`, to a client socket that doesn't read for 300 ms. Excerpt:
  ```
   118 ms channelWritabilityChanged isWritable=false pending=66304 B
   127 ms channelWritabilityChanged isWritable=true pending=24864 B
   128 ms channelWritabilityChanged isWritable=false pending=66304 B
   128 ms pump wrote 5 chunks, total=104 KiB, isWritable=false, pending=66304 B, bytesBeforeUnwritable=0
   128 ms pump wrote 8 chunks, total=104 KiB, isWritable=false, pending=66304 B, bytesBeforeUnwritable=0
   401 ms client starts reading
   402 ms channelWritabilityChanged isWritable=true pending=24864 B
   ... (≈300 more flips while 4 MiB drains)
   453 ms pump wrote 4 chunks, total=4096 KiB, isWritable=true, pending=58016 B, bytesBeforeUnwritable=7521
  ```
  Writability turns false just above 64 KiB pending and true again below 32 KiB. The two "pump wrote" lines carry the same timestamp, and the 5-chunk line was logged first. That shows `channelWritabilityChanged(true)` fired **inside** `flush()` and re-entered `pump()`, which finished before the outer call logged its line. Handlers must be re-entrancy-safe.
- **Observed close() data loss** (local run): `close() right after last flush -> client received 4136960 of 4194304 bytes`. 57,344 bytes were lost, matching the ~58 KB still pending. The fix: `ctx.writeAndFlush(Unpooled.EMPTY_BUFFER).addListener(ChannelFutureListener.CLOSE)`, i.e. close when the last write completes, gave `4194304 of 4194304 bytes`.
- **Observed backpressure** (local run, `NettyDepth backpressure`). Echo server; the client writes 16 MiB as fast as possible and reads 16 KiB at a time with a 20 ms pause per 128 KiB; socket buffers are 32 KiB:
  ```
  backpressure=false -> peak ChannelOutboundBuffer pending = 2,317,248 bytes   (JUnit run of the same code: 16,202,075 bytes)
  backpressure=true  -> peak ChannelOutboundBuffer pending =   129,312 bytes   (JUnit run: 129,312)
  ```
  Without backpressure the peak varies widely (2.3 MB to 16.2 MB, i.e. up to the whole payload sitting in heap or direct memory). With backpressure it stays at ~2× the high water mark. The backpressure handler:
  ```java
  public void channelRead(ChannelHandlerContext ctx, Object msg) { ctx.write(msg); }
  public void channelReadComplete(ChannelHandlerContext ctx) {
    ctx.flush();
    if (!ctx.channel().isWritable()) ctx.channel().config().setAutoRead(false);   // stop reading from a peer we can't write to
  }
  public void channelWritabilityChanged(ChannelHandlerContext ctx) {
    if (ctx.channel().isWritable()) ctx.channel().config().setAutoRead(true);
    ctx.fireChannelWritabilityChanged();
  }
  ```
  In a proxy, toggle the *inbound* channel's autoRead from the *outbound* channel's writability.

**Pooling and allocator details (lesson writers):**
- `ByteBufUtil` picks the default allocator from `io.netty.allocator.type`, default `"adaptive"`, alternatives `"unpooled"` and `"pooled"`. — [netty-buffer-4.2.20.Final-sources.jar, ByteBufUtil.java](https://repo.maven.apache.org/maven2/io/netty/netty-buffer/4.2.20.Final/)
- The adaptive allocator (`AdaptivePoolingAllocator`, marked `@UnstableApi`): "An auto-tuning pooling allocator, that follows an anti-generational hypothesis. The allocator is organized into a list of Magazines... each thread picks a magazine based on the id of the thread... If contention is detected above a certain threshold, the number of magazines are increased... The preferred chunk size is one that is big enough to service 10 allocations of the 99-percentile size." Magazines share excess chunks through a chunk cache. — [AdaptivePoolingAllocator.java](https://repo.maven.apache.org/maven2/io/netty/netty-buffer/4.2.20.Final/)
- Tunables present in 4.2.20 source:
  - pooled: `io.netty.allocator.numHeapArenas`, `numDirectArenas`, `pageSize`, `maxOrder`, `smallCacheSize`, `normalCacheSize`, `maxCachedBufferCapacity`, `cacheTrimInterval(Millis)`, `useCacheForAllThreads` (default **false**)
  - adaptive: `chunkSize`, `magazineBufferQueueCapacity`, `useCachedMagazinesForNonEventLoopThreads`, `lowMemory`, ...

  — [PooledByteBufAllocator.java / AdaptivePoolingAllocator.java](https://repo.maven.apache.org/maven2/io/netty/netty-buffer/4.2.20.Final/)
- Leak detection basics (levels, sampling 1/128, PARANOID for tests, `ByteBufUtil.setLeakListener`, de-duplicated reports) are in `nio_event_loops.md`, Q4.

### Inferences
- `useCacheForAllThreads=false` suggests pooled thread-local caches serve Netty event-loop (FastThreadLocal) threads by default, not arbitrary application threads. That makes buffer allocation from your own executors more expensive. Inferred from the property name and default; not measured.
- Teach writability as Netty's version of the OP_WRITE logic from io-02: the outbound buffer is your "pending" ByteBuffer, and autoRead is your OP_READ toggle.

### Gaps
- Not run: `ChunkedWriteHandler`, the HTTP codecs, `FlowControlHandler`.
- No allocator benchmarks (pooled vs adaptive).

---

## Q3. Vert.x depth: verticles, deployment, contexts, event bus, vertx-junit5

### Takeaway
[Vert.x 5.2.3]
- Verticles implement `Deployable`; `VerticleBase` has `Future<?> start()`. They deploy with `deployVerticle(Supplier<? extends Deployable>, new DeploymentOptions().setInstances(n).setThreadingModel(...))`.
- Each instance gets its own **context**: an event-loop context pinned to one event loop, a worker context, or a virtual-thread context. Handlers registered there always run on that context.
- The event bus offers:
  - point-to-point `send`/`request` (non-strict round-robin across consumers);
  - `publish` to all consumers;
  - request/reply with a default 30 s timeout and typed `ReplyException` failures (`NO_HANDLERS`, `TIMEOUT`, `RECIPIENT_FAILURE`).

  Custom types need a `MessageCodec`; locally, its `transform()` decides whether the consumer gets the same instance.
- vertx-junit5 injects `Vertx` and `VertxTestContext`, with a 30 s default timeout. Assertions must go inside `verify(...)`/`succeeding(...)`, or failures become timeouts. It works with JUnit 6.1.3.

### Cited Findings

**Verticles and deployment:**
- "Verticle classes must implement the `Deployable` interface." There are standard (event-loop), worker and virtual-thread verticles. "Worker verticle instances are never executed concurrently by Vert.x by more than one thread, but can executed by different threads at different times." "A virtual thread verticle is just like a standard verticle but it's executed using virtual threads, rather than using an event loop." Multiple instances are "useful for scaling easily across multiple cores". — [Vert.x 5.2.3 core docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- Doc/API mismatch [5.2.3]: the docs say to pass "a `Callable<Deployable>`" for multiple instances. javap shows `deployVerticle(Supplier<? extends Deployable>, DeploymentOptions)` and `deployVerticle(Class<? extends Deployable>, DeploymentOptions)`. `Greeter::new` compiled against the `Supplier` overload. — [Vert.x 5.2.3 core docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc); (local javap)
- Context: "Usually a context is an *event-loop context* and is tied to a specific event loop thread. So executions for that context always occur on that exact same event loop thread. In the case of worker verticles and running inline blocking code a worker context will be associated". `Vertx.getOrCreateContext()` reuses the current thread's context if one exists. Contexts carry `runOnContext`, local data and `config()`. — [Vert.x 5.2.3 core docs](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc)
- Virtual-thread verticles: "You can use `Future#await` to suspend the current virtual thread until the awaited result is available... When a virtual thread awaits for a result and the verticle needs to process a task, a new virtual thread is created to handle this task... IMPORTANT: Like any verticle at most one task is executed at the same time."
  - "if you are reading a field before an `await` call and reusing the value after the call, you should keep in mind that this value might have changed."
  - Blocking without `await` (e.g. `ReentrantLock#lock`) makes it behave "like a worker verticle, yet using virtual threads".
  - "Thread locals are only reliable within the execution of a context task."
  - Requires Java 21+.

  — [virtualthreads.adoc @ 5.2.3](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/virtualthreads.adoc)
- `Future` has `await()`, `await(Duration)`, `await(long, TimeUnit)` and the static `Future.await(Future)` [5.2.3, javap]. (local)

**Event bus (docs @ 5.2.3):**
- "There is a single event bus instance for every Vert.x instance". It supports "publish/subscribe, point-to-point, and request-response messaging". Addresses are plain strings. With point-to-point, Vert.x "will then route them to just one of the handlers registered at that address... chosen using a non-strict round-robin algorithm".
- Delivery is "Best-effort delivery... make handlers idempotent". Ordering: "Vert.x will deliver messages to any particular handler in the same order they were sent from any particular sender".
- Timeouts: "The default timeout is 30 seconds." Failures include "no handlers available" and "the recipient has explicitly failed the message using `Message#fail`".
- Codecs: you "define and register a `MessageCodec`". Use `registerDefaultCodec` for a type, or pass the codec name in `DeliveryOptions`. Built-in codecs cover basic types, `Buffer`, `JsonObject`/`JsonArray`, `ClusterSerializable` and `Serializable`; the last two are rejected by default in clustered mode.
- `MessageConsumer#processor(...)` signals async completion for tracing. Request/reply is the exception.

  — [eventbus.adoc @ 5.2.3](https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/eventbus.adoc)
- API [5.2.3, javap]:
  - `MessageCodec<S,R>` methods: `encodeToWire(Buffer,S)`, `decodeFromWire(int,Buffer)`, `transform(S)`, `name()`, `systemCodecID()`.
  - `ReplyFailure` values: `TIMEOUT`, `NO_HANDLERS`, `RECIPIENT_FAILURE`, `ERROR`.
  - `EventBus` methods: `request(String,Object[,DeliveryOptions])` returns `Future<Message<T>>`; `localConsumer(...)`; `registerDefaultCodec(Class,MessageCodec)`; `codecSelector(Function)`.
- **Observed** (local run, `VertxDepth`: 2 `Greeter` instances, one event loop each):
  ```
  deployed 2 instances of Greeter, deploymentID=1
  request greet #0 -> hello dev0 from instance#1 on vert.x-eventloop-thread-1 eventLoopCtx=true workerCtx=false model=EVENT_LOOP
  request greet #1 -> hello dev1 from instance#2 on vert.x-eventloop-thread-0 eventLoopCtx=true workerCtx=false model=EVENT_LOOP
  request greet #2 -> hello dev2 from instance#1 on vert.x-eventloop-thread-1 ...
  request greet #3 -> hello dev3 from instance#2 on vert.x-eventloop-thread-0 ...
    [news] instance#1 got 'release 1.0' header src=main
    [news] instance#2 got 'release 1.0' header src=main
  request nobody -> ReplyException failureType=NO_HANDLERS failureCode=-1 message=No handlers for address nobody
  request fail -> ReplyException failureType=RECIPIENT_FAILURE failureCode=42 message=boom from instance#2
  request silent (sendTimeout=300ms) -> TIMEOUT after 308 ms: Timed out after waiting 300(ms) for a reply. address: __vertx.reply.7, repliedAddress: silent
  DeliveryOptions.DEFAULT_TIMEOUT = 30000 ms
  request orders (custom local codec) -> instance#2 got Order[id=o-1, qty=3] sameInstance=true
  [WORKER verticle] start() on vert.x-worker-thread-0 eventLoopCtx=false workerCtx=true model=WORKER
      reply handled on vert.x-worker-thread-0 eventLoopCtx=false workerCtx=true model=WORKER
  [VIRTUAL_THREAD verticle] start() on vert.x-virtual-thread-0(virtual) eventLoopCtx=false workerCtx=false model=VIRTUAL_THREAD
      awaited reply: hello vt from instance#2 on vert.x-eventloop-thread-0 ...
      resumed on vert.x-virtual-thread-0(virtual) ... model=VIRTUAL_THREAD
  ```
  What it shows:
  - Point-to-point round-robins strictly here (1, 2, 1, 2); the docs only promise "non-strict".
  - Each instance sits on its own event loop.
  - The reply future completes back on the *caller's* context (worker → worker thread; virtual → same virtual thread).
  - With an identity `transform()`, the local codec hands over the **same object instance**, so senders must not mutate messages after sending.
- Local-only codec used (ran as shown):
  ```java
  final class OrderCodec implements MessageCodec<Order, Order> {
    public void encodeToWire(Buffer b, Order o) { throw new UnsupportedOperationException("local only"); }
    public Order decodeFromWire(int pos, Buffer b) { throw new UnsupportedOperationException("local only"); }
    public Order transform(Order o) { return o; }      // identity: zero-copy, but shared mutable state
    public String name() { return "order-local"; }
    public byte systemCodecID() { return -1; }         // -1 = user codec
  }
  vertx.eventBus().registerDefaultCodec(Order.class, new OrderCodec());
  ```

**vertx-junit5 (docs @ 5.2.3 plus source):**
- Why it exists: `listen` "does not block"; the callback "will be executed from a Vert.x event loop thread"; the test may exit early; and "any exception such as one thrown by a failed assertion cannot be capture by the JUnit runner".
- `VertxTestContext` provides `completeNow`/`failNow`, `succeedingThenComplete`/`failingThenComplete`, `succeeding(h)`/`failing(h)` (which "can only make a test fail"), `verify(block)`, and `checkpoint(n)` + `flag()`. Checkpoints "should be created only from the test case main thread".
- Injection scopes: a `Vertx` injected in `@BeforeAll` is shared across the class; one injected in `@BeforeEach` is shared with that test and `@AfterEach`. Injected instances are closed automatically.
- Override the timeout with `@io.vertx.junit5.Timeout`. Configure options via a JSON file named by `VERTX_PARAMETER_FILENAME` or `-Dvertx.parameter.filename`, e.g. to extend blocked-thread limits while debugging.
- Vert.x 5 warning: clients rely on `Cleaner`, so an unreachable client "may close its underlying pool *non-deterministically*" (`VertxException: Pool closed`). Keep clients in fields during tests.

  — [vertx-junit5 index.adoc @ 5.2.3](https://raw.githubusercontent.com/vert-x3/vertx-junit5/5.2.3/src/main/asciidoc/index.adoc)
- Default timeout: `VertxExtension.DEFAULT_TIMEOUT_DURATION = 30`, `DEFAULT_TIMEOUT_UNIT = TimeUnit.SECONDS`. — [vertx-junit5-5.2.3-sources.jar, VertxExtension.java](https://repo.maven.apache.org/maven2/io/vertx/vertx-junit5/5.2.3/)
- JUnit 6 compatibility: under `junit-bom 6.1.3`, Maven resolved vertx-junit5 5.2.3's JUnit dependencies to `junit-jupiter-api/params/engine 6.1.3`. All vertx-junit5 tests below passed under Surefire 3.5.4. (local run; `mvn dependency:tree`)
- **Observed pitfall** (local run, `VertxPitfallTest`, intentionally failing):
  ```
  assertionWithoutVerifyIsSwallowed -- Time elapsed: 2.638 s <<< ERROR!
  java.util.concurrent.TimeoutException:
  The test execution timed out. Make sure your asynchronous code includes calls to either VertxTestContext#completeNow(), VertxTestContext#failNow() or Checkpoint#flag()
  (the AssertionFailedError "expected: 2 but was: 1" is only printed to the log, from the event-loop thread)

  assertionInsideVerifyFailsTheTest -- Time elapsed: 0.059 s <<< FAILURE!
  java.lang.AssertionError: org.opentest4j.AssertionFailedError: expected: 2  but was: 1
  ```

### Inferences
- For io-05, teach the context as the unit of serialisation. It plays the role of Netty's per-channel event loop, generalised to verticles, timers and event-bus consumers. "Same context ⇒ no concurrent execution ⇒ no locks needed" is the payoff. The `executeBlocking` ordered-per-context behaviour from the previous notes is the flip side.

### Gaps
- Not run: clustered event bus, `MessageConsumer.processor`, `codecSelector`.
- Event-bus round-robin fairness under load was not tested.

---

## Verified URLs

Fetched directly (curl, HTTP 200, content read):
- https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/eventbus.adoc
- https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/virtualthreads.adoc
- https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc (fetched in the first round, re-read for this round)
- https://raw.githubusercontent.com/vert-x3/vertx-junit5/5.2.3/src/main/asciidoc/index.adoc
- https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/http.xml
- https://raw.githubusercontent.com/apache/tomcat/main/webapps/docs/config/http.xml
- https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/executor.xml
- https://raw.githubusercontent.com/apache/tomcat/11.0.x/build.properties.default

Read via sparse `git clone` of https://github.com/jetty/jetty.project at tag `jetty-12.1.14`, into the scratchpad. These are canonical blob URLs; I did not load the HTML pages:
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/io.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/threads.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http2.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http3.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/11-to-12.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/12.0-to-12.1.adoc
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/antora.yml
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/QueuedThreadPool.java
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/ReservedThreadExecutor.java
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/VirtualThreadPool.java
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/thread/strategy/AdaptiveExecutionStrategy.java
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-io/src/main/java/org/eclipse/jetty/io/SelectorManager.java
- https://github.com/jetty/jetty.project/blob/jetty-12.1.14/jetty-core/jetty-server/src/main/java/org/eclipse/jetty/server/AbstractConnector.java
- Tag listing via `git ls-remote --tags https://github.com/jetty/jetty.project.git`

Read from Maven Central artifacts (downloaded with `mvn dependency:copy-dependencies`, inspected with javap/unzip):
- https://repo.maven.apache.org/maven2/org/eclipse/jetty/jetty-server/12.1.14/ (with jetty-util, jetty-io, jetty-http 12.1.14, jars and `-sources.jar`)
- https://repo.maven.apache.org/maven2/io/vertx/vertx-junit5/5.2.3/ (jar and `-sources.jar`)
- https://repo.maven.apache.org/maven2/io/vertx/vertx-core/5.2.3/
- https://repo.maven.apache.org/maven2/io/netty/netty-codec-base/4.2.20.Final/, .../netty-transport/4.2.20.Final/, .../netty-buffer/4.2.20.Final/, .../netty-handler/4.2.20.Final/ (`-sources.jar`)
- https://repo.maven.apache.org/maven2/org/junit/junit-bom/6.1.3/

---

## Teaching notes

### Misconceptions
1. **"Jetty is a thread-per-request server like Tomcat."** Jetty 12 picks per task. Non-blocking handlers run on the selector thread (PC), and blocking ones usually run on the selector thread while a reserved thread takes over selecting (EPC). Evidence: the `pcRunTask` and `epcRunTask` frames above. Tomcat's NIO connector does dispatch to an executor (200 threads by default).
2. **"Extending `Handler.Abstract.NonBlocking` makes my code non-blocking."** It is a *promise* to Jetty, not a transformation. Break it and you get event-loop-style lock-ups ("you risk a server lock-up").
3. **"`VirtualThreadPool(8)` is a pool of 8 virtual threads."** It spawns a virtual thread per task and caps concurrency with a semaphore, which the selector and acceptor tasks also use. Observed: 3.0–3.5 s for 40×500 ms, against 0.53–0.55 s with `QueuedThreadPool` + virtual executor.
4. **"A bounded Jetty queue protects me from overload."** Jetty requires an unbounded queue and limits load with a QoS handler instead.
5. **"Netty buffers writes for me, so I can just write."** Ignoring `isWritable()` let up to 16 MB pile up in the outbound buffer (observed peak 2.3–16.2 MB). Respecting it kept the peak at ~129 KB.
6. **"`close()` after `flush()` sends everything."** It dropped 56 KiB in my run. Close from the last write's future.
7. **"The event bus is a message broker."** It is best-effort and in-memory (or clustered), with a 30 s default reply timeout. No persistence; make handlers idempotent.
8. **"An assertion in a Vert.x callback fails the test."** Without `verify`, it surfaced as a 2.6 s timeout. Inside `verify`, it failed in 0.059 s.

### Analogies
- **AdaptiveExecutionStrategy = a chef who cooks what they just took off the delivery truck** ("eat what you kill"): ingredients are still warm in that CPU's cache. If the dish might take long (BLOCKING), a standby cook (reserved thread) takes over receiving deliveries first. With no standby cook, the dish goes to the kitchen queue (PEC).
- **Netty water marks = a bathtub with an overflow line.** Stop the tap (`autoRead=false`) when the water passes the high line, and reopen it when it drops below the low line.
- **Vert.x context = a desk with one chair.** Everything registered at that desk is handled by whoever sits there, one item at a time: an event loop, a worker, or a virtual thread.

### Lab designs, run as JUnit 6.1.3 tests (all passed: 13 tests, `BUILD SUCCESS`)
Tests are in `proj2/src/test/java/labs/`. Every server binds `127.0.0.1:0`. Run time was 2.6 s for Jetty, 3.5 s for Netty and 1.5 s for Vert.x. Class-level `@Timeout(20)` (JUnit) for Jetty/Netty; vertx-junit5's own timeout for Vert.x.

1. **Jetty (io-07): `JettyLabTest`**
   - `handlerDeclaresInvocationType`: `new Blocking(0).getInvocationType() == BLOCKING`; `new NonBlocking().getInvocationType() == NON_BLOCKING`. Passed.
   - `asyncHandlerCompletesCallbackLater`: POST "ping" → 200, body contains `body='ping'`. Passed.
   - `smallPlatformPoolSerializesBlockingHandlers`: `QueuedThreadPool(12)`, 30 concurrent requests × 300 ms, assert ≥ 600 ms. Observed 1,380 ms.
   - `virtualThreadsExecutorRunsBlockingHandlersOnVirtualThreads`: the same with `setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("lab-vt-"))`. Assert < 600 ms and every body contains `virtual=true`. Observed 334 ms.
   - Exercise idea: the student implements `Blocking`/`AsyncEcho` and configures the pool. Grading uses the assertions above.
   - Extension: make the student declare a handler `NonBlocking` that sleeps, and observe the latency of a second connection. Not run.
2. **Netty codecs (io-04): `NettyLabTest`**
   - `encoderWritesLengthTypeAndUtf8`: `Msg(1,"hello")` encodes to hex `000000060168656c6c6f`.
   - `decoderReassemblesFragmentedFrames`: slices [0,3) → `writeInbound` returns false; [3,11) → true, `readInbound()` = `Msg(1,"hello")`, then null; [11,end) → `Msg(7,"netty 4.2")`; `finish()` false.
   - `oversizedFrameIsRejected`: length 5000 → `TooLongFrameException` containing "exceeds 1024". Full message: `Adjusted frame length exceeds 1024: 5004 - discarded`.

   All passed. Run with `-Dio.netty.leakDetection.level=paranoid`, the demo reported no leaks.
3. **Netty flow control (io-04): `NettyLabTest`**
   - `backpressureBoundsOutboundBuffer`: with backpressure, peak pending < 512 KiB (observed 129,312 B); without, peak greater than with (observed 16,202,075 B).
   - `closingAfterLastWriteFutureDeliversEverything`: the client receives exactly 4,194,304 bytes.
   - Don't grade "close() loses data" as a test: it is timing-dependent, though it lost 57,344 B in every run I made. Use it as a demo.
   - The peak without backpressure varies (2.3–16.2 MB), so only assert a relation or an upper bound for the backpressure case.
4. **Vert.x event bus (io-05): `VertxLabTest`, `@ExtendWith(VertxExtension.class)`**
   - `@BeforeEach` deploys `Greeter` ×2 via `tc.succeedingThenComplete()`.
   - `requestReply`: body starts with `hello lab from instance#` and contains `vert.x-eventloop-thread`.
   - `publishReachesEveryConsumer`: `tc.checkpoint(3)`, flagged by 3 consumers.
   - `noHandlersFailsFast`: `failureType() == NO_HANDLERS`.
   - `silentConsumerTimesOut`: `setSendTimeout(200)` gives `TIMEOUT`, under `@io.vertx.junit5.Timeout(3 s)`.

   All passed.
5. **Vert.x testing pitfall (io-05, demo, deliberately red): `VertxPitfallTest`.** Expected outcomes are recorded above: TimeoutException at about 2.6 s versus AssertionError at 0.059 s. Keep it out of the default test run, e.g. tag it and exclude the tag in Gradle.

Gradle and wiring notes for the labs repo:
- `labs/build.gradle.kts` already pins netty 4.2.20.Final and vertx 5.2.3. Add `org.eclipse.jetty:jetty-server:12.1.14` and `io.vertx:vertx-junit5:5.2.3`. The JUnit BOM 6.1.3 manages vertx-junit5's JUnit dependencies; this worked under Maven.
- Add an SLF4J binding (e.g. `org.slf4j:slf4j-simple`) to silence Jetty's NOP-logger warning.
- Use `java.net.http.HttpClient` with `.proxy(HttpClient.Builder.NO_PROXY)` for localhost calls in proxied CI environments.
- Fully qualify `io.vertx.junit5.Timeout`, which clashes with `org.junit.jupiter.api.Timeout`.
