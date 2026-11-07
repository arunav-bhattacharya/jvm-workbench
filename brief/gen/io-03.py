import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l03"
K = "kotlin/workbench/nio/l03"
read = lambda p: (ROOT / p).read_text()

boxes = [  # x, width, class, line1, line2
    (24, 60, "box", "head", "socket"),
    (100, 116, "box-a", "frame lines", "inbound"),
    (232, 116, "box-a", "decode UTF-8", "inbound"),
    (364, 116, "box-b", "encode UTF-8", "outbound"),
    (496, 116, "box-a", "QuoteHandler", "inbound"),
    (628, 60, "box", "tail", ""),
]
parts = []
for x, w, cls, l1, l2 in boxes:
    parts.append(f'<rect class="{cls}" x="{x}" y="88" width="{w}" height="52" rx="8"/>')
    parts.append(f'<text class="t-s" x="{x + w // 2}" y="{110 if l2 else 119}" text-anchor="middle">{l1}</text>')
    if l2:
        parts.append(f'<text class="t-s t-m" x="{x + w // 2}" y="128" text-anchor="middle">{l2}</text>')
FIG = (
    '<svg viewBox="0 0 712 262" role="img" aria-label="A Netty pipeline from head to tail: frame decoder, string decoder, '
    'string encoder and the business handler. Inbound reads flow from head to tail, writes flow from the handler back to the head, '
    'and one event-loop thread runs all of it">'
    '<text class="t-s t-a" x="356" y="40" text-anchor="middle">inbound: bytes in, channelRead flows head to tail</text>'
    '<line class="ln-a" x1="54" y1="56" x2="654" y2="56" marker-end="url(#arr)"/>'
    + "".join(parts)
    + '<line class="ln" x1="554" y1="176" x2="58" y2="176" marker-end="url(#arr)"/>'
    '<text class="t-s t-b" x="306" y="198" text-anchor="middle">outbound: ctx.writeAndFlush flows toward the head, through the encoder</text>'
    '<rect class="box-dim" x="24" y="216" width="664" height="32" rx="8"/>'
    '<text class="t-s" x="356" y="237" text-anchor="middle">one event-loop thread runs every handler of this channel, one event at a time</text>'
    '</svg>'
)

L = {
 "id": "io-03",
 "title": "Netty: the event loop and the channel pipeline",
 "minutes": 35,
 "goal": "By the end you can build a Netty 4.2 server with MultiThreadIoEventLoopGroup, explain which thread runs your handlers and in what order, test a pipeline with EmbeddedChannel, and move blocking work off the event loop.",
 "warmup": {
  "q": "A Netty server runs 2 worker event loops. Six clients connect. The handler for client 3 calls a JDBC query that takes 500 ms. Which clients notice?",
  "options": [
   "Only client 3",
   "The clients that share client 3's event loop, roughly half of them",
   "All six clients, because Netty serializes the whole server",
   "None of them: Netty runs each read on a fresh thread"
  ],
  "answer": 1,
  "why": "Netty assigns each new channel to one loop of the group, round-robin, and keeps it there for life. Every handler call for those channels runs on that loop's one thread. Clients 1, 3 and 5 share a loop, so 1 and 5 wait behind client 3's query. The clients on the other loop never notice."
 },
 "sections": [
  {
   "h": "An event loop is one thread that owns its channels",
   "body": """Netty is the select loop from the last lesson, written once and written well. Each piece you wrote by hand has a Netty name, and each fixes a bug you met there:

| Your loop in lesson 2 | Netty | Why it exists |
|---|---|---|
| one thread running `select()` | `EventLoop`, several in an `EventLoopGroup` | one loop per core instead of one per server |
| the `Conn` attachment | `Channel` and its `ChannelPipeline` of handlers | per-connection state and logic in small pieces |
| `flip()` and `compact()` by hand | `ByteBuf`, with separate read and write indexes | no mode to get wrong (lesson 4) |
| pending bytes and arming `OP_WRITE` | the channel's outbound buffer | Netty sets and clears `OP_WRITE` for you |
| dropping `OP_READ` when full | `autoRead` and writability | backpressure as a setting (lesson 4) |
| nothing: only the loop may touch the selector | a task queue on every loop | any thread can hand the loop work safely |

So an event loop is one thread that runs a selector over many channels, plus that queue of tasks. In Netty 4.2 you build a group by naming the IO handler, the transport-specific part:

```java
EventLoopGroup boss = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());   // accepts connections
EventLoopGroup workers = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());  // serves them
Channel server = new ServerBootstrap()
        .group(boss, workers)
        .channel(NioServerSocketChannel.class)
        .childHandler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ch.pipeline().addLast(new LineBasedFrameDecoder(64), new StringDecoder(UTF_8),
                        new StringEncoder(UTF_8), new QuoteHandler());
            }
        })
        .bind(8080).sync().channel();
```

```kotlin
val boss = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())     // accepts connections
val workers = MultiThreadIoEventLoopGroup(NioIoHandler.newFactory())    // serves them
val server = ServerBootstrap()
    .group(boss, workers)
    .channel(NioServerSocketChannel::class.java)
    .childHandler(object : ChannelInitializer<SocketChannel>() {
        override fun initChannel(ch: SocketChannel) {
            ch.pipeline().addLast(LineBasedFrameDecoder(64), StringDecoder(UTF_8),
                StringEncoder(UTF_8), QuoteHandler())
        }
    })
    .bind(8080).sync().channel()
```

If you learned Netty 4.1, you wrote `new NioEventLoopGroup()`. Netty 4.2 deprecated it, along with its epoll and kqueue cousins, and `javac -Xlint:deprecation` says so: `warning: [deprecation] NioEventLoopGroup in io.netty.channel.nio has been deprecated`. The replacement is always `MultiThreadIoEventLoopGroup` plus a factory: `NioIoHandler`, `EpollIoHandler`, `KQueueIoHandler` or `IoUringIoHandler`. The bootstrap still names the matching channel class.

The boss group only accepts connections and hands each one to a worker loop, so one boss thread is plenty for one listening port. Small servers often pass a single group to `.group(group)` and let the same loops accept and serve. The lab does that, with one loop, so that you can see a blocked loop clearly.

Without a thread count, a group gets two loops per core, so the demo prints 8 on a 4-core machine. Each new connection is registered with one loop, round-robin, and stays there for life:

```text
client port 59604 registered on multiThreadIoEventLoopGroup-4-1, inEventLoop=true
client port 59620 registered on multiThreadIoEventLoopGroup-4-2, inEventLoop=true
client port 59634 registered on multiThreadIoEventLoopGroup-4-1, inEventLoop=true
```

That pinning is why Netty handlers rarely need locks: every event for a channel runs on its loop's one thread, one after another. It is also why one slow handler hurts. Every other channel on that loop waits behind it.""",
   "try": {
    "title": "See which loop owns each connection",
    "minutes": 4,
    "steps": [
     "Open `EventLoopDemo.java` (or `EventLoopDemo.kt`). It starts a server with one acceptor loop and two worker loops, then connects four clients one after another.",
     "Predict the thread name for the third and fourth client, and what `inEventLoop()` returns inside the handler.",
     "Run it. Then change the worker group to `new MultiThreadIoEventLoopGroup(1, ...)` and run it again."
    ],
    "code": {"lang": "java", "title": "EventLoopDemo.java", "src": read(f"{lab}/demo/{P}/EventLoopDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.EventLoopDemo",
             "file": f"{lab}/demo/{P}/EventLoopDemo.java",
             "alt": {"lang": "kotlin", "title": "EventLoopDemo.kt", "src": read(f"{lab}/demo/{K}/EventLoopDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.EventLoopDemoKt",
                     "file": f"{lab}/demo/{K}/EventLoopDemo.kt"}},
    "expect": "The default group reports 8 loops on a 4-core machine. The four clients alternate between `multiThreadIoEventLoopGroup-4-1` and `-4-2`, and each client's bytes are handled on the same thread that registered it, with `inEventLoop=true`. With one worker loop, all four land on the same thread."
   }
  },
  {
   "h": "The pipeline: reads flow in, writes flow out",
   "body": """Every channel has a `ChannelPipeline`: a linked list of handlers between a head, next to the socket, and a tail. Two kinds of traffic move through it.

Each handler gets a `ChannelHandlerContext`, usually called `ctx`: its own slot in the pipeline, with methods to pass an event to the next handler or to start a write from that slot. Inbound events start at the head and move toward the tail: `channelActive` when the connection opens, `channelRead` for each message, `channelReadComplete` after a batch of reads, and `exceptionCaught` when something fails. Inbound handlers transform the message on its way. In the quote server, the frame decoder turns a stream of bytes into one `ByteBuf` per line, and `StringDecoder` turns that into a `String`, so the last handler only ever sees whole lines.

Outbound operations go the other way. `write`, `flush` and `close` start where you call them and move toward the head. `StringEncoder` sits on that path and turns your `String` back into bytes. So the order of `addLast` is the order inbound events see the handlers, and the reverse of the order writes see them.

One detail decides which handlers a write passes. `ctx.writeAndFlush(msg)` starts at the current handler and goes toward the head, skipping everything after it. `ctx.channel().writeAndFlush(msg)` starts at the tail and passes every outbound handler. Inside a handler, use `ctx` unless you really want the whole pipeline.

This section's demo puts a tap between the stages and feeds one line in pieces:

```text
writeInbound("hel")
writeInbound("lo\\nwor")
   in,  after framing : ByteBuf "hello"
   in,  business sees : String "hello"
   out, to the wire   : ByteBuf "HELLO\\n"
100-byte line -> TooLongFrameException: frame length (100) exceeds the allowed maximum (64)
finish() = false
```

The first fragment produced nothing: the decoder kept the bytes and waited for the end of the line. That is lesson 2's framing problem, solved once inside the pipeline. The 64-byte limit matters as much. Without it, a client that never sends a newline makes the decoder buffer forever.

The demo uses `EmbeddedChannel`, which runs a pipeline with no socket and no real event loop. `writeInbound` pushes bytes in, `readOutbound` returns what the handlers wrote, and `finish()` says whether anything was left over. It is the fastest way to test a handler, and this lesson's lab uses it.""",
   "figure": {"svg": FIG, "caption": "Reads travel from the head through the decoders to your handler; your writes travel back through the encoder to the head. One thread runs all of it."},
   "try": {
    "title": "Move the tap past the encoder",
    "minutes": 4,
    "steps": [
     "Run `PipelineDemo` (or `PipelineDemoKt`) and match each printed line to a handler in the figure.",
     "In the `EmbeddedChannel` constructor, move the outbound tap so it comes right after `new StringEncoder(UTF_8)` instead of before it.",
     "Predict what `out, to the wire` prints now, then run it again."
    ],
    "code": {"lang": "java", "title": "PipelineDemo.java", "src": read(f"{lab}/demo/{P}/PipelineDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.PipelineDemo",
             "file": f"{lab}/demo/{P}/PipelineDemo.java",
             "alt": {"lang": "kotlin", "title": "PipelineDemo.kt", "src": read(f"{lab}/demo/{K}/PipelineDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.PipelineDemoKt",
                     "file": f"{lab}/demo/{K}/PipelineDemo.kt"}},
    "expect": "Before the move the tap prints `ByteBuf \"HELLO\\n\"`: the write passed the encoder first. After the move it prints `String \"HELLO\\n\"`, because the write now reaches the tap before the encoder. Writes travel from the business handler toward the head, so position in the list decides what each outbound handler sees."
   }
  },
  {
   "h": "Never block the event loop",
   "body": """Handlers run on the event-loop thread. A handler that sleeps, waits on a lock, or calls JDBC holds that thread, and every other channel on the loop waits with it. This section's demo measures it with one event loop and two clients. Client A asks for `SLOW`, which sleeps 1 s to stand in for a database call. Client B asks for `FAST` 50 ms later:

```text
[blocking in the handler]
   event-loop lag probe: 1010 ms
   FAST reply after 1011 ms: FAST on multiThreadIoEventLoopGroup-2-1
[dispatch to app pool]
   event-loop lag probe: 0 ms
   FAST reply after 2 ms: FAST on app-blocking-pool
```

The lag probe is a trick worth keeping: submit an empty task to the loop and time how long it waits to run. On a healthy loop it is close to 0.

Netty 4.1 offered a shortcut: `pipeline.addLast(executorGroup, "name", handler)` ran one handler on a separate `EventExecutorGroup`. Netty 4.2 deprecated those overloads, and compiling the old call prints `warning: [deprecation] addLast(EventExecutorGroup,String,ChannelHandler) in ChannelPipeline has been deprecated`. The commit that did it (d64340b) says per-handler executors caused more problems than they solved and that it is "much better to dispatch it manually".

Manual dispatch is three lines. Hand the slow part to your own executor and write the reply from there:

```java
@Override
protected void channelRead0(ChannelHandlerContext ctx, String line) {
    blockingPool.execute(() -> {                   // 1. leave the event loop
        String quote = quoteDao.findQuote(line);   // 2. block here: JDBC, a 120 ms issuer call
        ctx.writeAndFlush(quote + "\\n");           // 3. safe from any thread
    });
}
```

```kotlin
override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    blockingPool.execute {                         // 1. leave the event loop
        val quote = quoteDao.findQuote(line)       // 2. block here: JDBC, a 120 ms issuer call
        ctx.writeAndFlush("$quote\\n")              // 3. safe from any thread
    }
}
```

Step 3 works because Netty checks `inEventLoop()` on every write. Called from another thread, the write becomes a task on the channel's own loop, so the pipeline still runs on one thread. If code in the executor needs the handler's own fields, hop back first with `ctx.executor().execute(...)`, so that state stays confined to the loop. Size `blockingPool` like any blocking pool: Little's law and the downstream's limits from lesson 1, or virtual threads.""",
   "try": {
    "title": "Block the loop, then free it",
    "minutes": 4,
    "steps": [
     "Open `BlockingLoopDemo.java` (or `BlockingLoopDemo.kt`). Predict the lag probe and the FAST reply time in both runs.",
     "Run it with the command below.",
     "In the blocking run, which thread produced the SLOW reply? In the dispatch run? Find the line in the code that decides it."
    ],
    "code": {"lang": "java", "title": "BlockingLoopDemo.java", "src": read(f"{lab}/demo/{P}/BlockingLoopDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.BlockingLoopDemo",
             "file": f"{lab}/demo/{P}/BlockingLoopDemo.java",
             "alt": {"lang": "kotlin", "title": "BlockingLoopDemo.kt", "src": read(f"{lab}/demo/{K}/BlockingLoopDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l03.BlockingLoopDemoKt",
                     "file": f"{lab}/demo/{K}/BlockingLoopDemo.kt"}},
    "expect": "Blocking: both the probe and the FAST reply wait about a second (1,010 and 1,011 ms here), and every reply comes from the event-loop thread. Dispatch: the probe reads 0 to a few ms, FAST answers in a few ms, and both replies come from `app-blocking-pool`. The work is the same; only the thread that waits changed."
   },
   "refs": [
    {"title": "Netty commit d64340b: deprecate ChannelPipeline.add*(EventExecutorGroup, ...)", "url": "https://github.com/netty/netty/commit/d64340b", "kind": "read"}
   ]
  },
  {
   "h": "What else Netty 4.2 changed",
   "body": """You'll read a lot of Netty 4.1 code and blog posts, so it helps to know what moved. These come from the official 4.2 migration guide and the 4.2.20 sources.

The default `ByteBuf` allocator is now the adaptive allocator. `ByteBufAllocator.DEFAULT` is an `AdaptiveByteBufAllocator`, and a plain `buffer(16)` comes back as a direct `AdaptiveByteBuf`. The migration guide says most workloads should see less memory use and that it was designed to work well with virtual threads. `-Dio.netty.allocator.type=pooled` brings back the old pooled allocator if you need it.

io_uring graduated from the incubator to a first-class transport. The package is now `io.netty.channel.uring`, the classes start with `IoUring`, and you use it like the others: `MultiThreadIoEventLoopGroup` with `IoUringIoHandler.newFactory()` and the `IoUring` channel classes. Lesson 8 measures it against epoll.

TLS clients now verify the server's hostname by default. Code that relied on the old behavior to connect to a test server with a mismatched certificate will start failing its handshake.

`netty-codec` was split into smaller modules, and the minimum Java version is now 8. And Netty 4.1 and 4.2 cannot be on the same classpath. That one matters in practice: Vert.x 5.2.3 pins Netty 4.2.20.Final, so a library that drags Netty 4.1 jars in next to it fails at runtime in confusing ways instead of with a clear version conflict. Check `./gradlew dependencies` for mixed `io.netty` versions before you debug anything else.

The threading rules did not change. A channel still belongs to one loop, handlers still run on it, and blocking it is still the most common way to make a Netty service slow.""",
   "try": {
    "title": "Switch the transport",
    "minutes": 3,
    "steps": [
     "In `EventLoopDemo`, change both groups to `EpollIoHandler.newFactory()` and the channel class to `EpollServerSocketChannel.class` (on macOS use `KQueueIoHandler` and `KQueueServerSocketChannel`). Run it. Predict first: do the thread names or the round-robin change?",
     "Now put the channel class back to `NioServerSocketChannel.class` but keep the epoll (or kqueue) factory. Predict what happens before you run it."
    ],
    "expect": "With matching factory and channel class the output looks the same: same thread names, same round-robin, because the threading model doesn't depend on the transport. With a mismatch the bind fails at once with `IllegalStateException: incompatible event loop type: io.netty.channel.SingleThreadIoEventLoop`: an NIO channel can only register with a loop whose IO handler is NIO. That is why the 4.2 migration guide reminds you to configure the channel class as well as the factory."
   }
  }
 ],
 "analogy": "A channel pipeline is the mail line in an office. Letters come in at the door, one clerk opens the envelopes (the frame decoder), the next reads the handwriting (the string decoder), and the last one writes the answer. Replies go back down the same line the other way, and a typist (the encoder) turns them into print before they leave. The event loop is one worker who carries each letter through every station for a fixed set of mailboxes. The analogy breaks because real clerks work at the same time. In Netty one thread carries each message through every handler, which is exactly why one slow station stops the whole line.",
 "in_your_world": "Every HTTP request to your Quarkus services arrives through a Netty pipeline: Vert.x runs its HTTP server on Netty event loops, so a blocked Vert.x event loop is a blocked Netty event loop. The same holds for other clients you probably run: Lettuce for Redis and the AWS SDK's async HTTP client are built on Netty too. When a payment API's p99 jumps while CPU is low, a thread dump that shows an event-loop thread inside JDBC, `Thread.sleep` or a `synchronized` block is the first thing to look for. When you upgrade Quarkus, also check that nothing in the build still pulls in Netty 4.1.",
 "mistake": "The common mistake is calling something blocking from a handler because \"it's only a few milliseconds\": a JDBC lookup, a `CompletableFuture.get()`, a synchronous HTTP client, even logging to a slow appender. A few milliseconds per message on a loop that serves 2,000 connections is a queue that never drains under load. The 4.1-era fix, `addLast(eventExecutorGroup, handler)`, is deprecated in 4.2. Dispatch the blocking part to your own executor and call `ctx.writeAndFlush` with the result, or move the work to a non-blocking client.",
 "compare": {
  "title": "Offloading a slow lookup from a Netty handler",
  "java": {"title": "QuoteHandler.java", "src": """final class QuoteHandler extends SimpleChannelInboundHandler<String> {
    private final Executor blocking;
    private final Function<String, String> lookup;

    QuoteHandler(Executor blocking, Function<String, String> lookup) {
        this.blocking = blocking;
        this.lookup = lookup;
    }

    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String line) {
        blocking.execute(() -> ctx.writeAndFlush(lookup.apply(line) + "\\n"));
    }
}"""},
  "kotlin": {"title": "QuoteHandler.kt", "src": """class QuoteHandler(
    private val blocking: Executor,
    private val lookup: (String) -> String,
) : SimpleChannelInboundHandler<String>() {
    override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
        blocking.execute { ctx.writeAndFlush(lookup(line) + "\\n") }
    }
}"""},
  "note": "At runtime these are the same class: Netty sees a `SimpleChannelInboundHandler<String>`, and the Kotlin lambda becomes a `Runnable` through SAM conversion. Kotlin saves the constructor boilerplate and takes a function type where Java needs `Function<String, String>`. One Kotlin-only temptation is worth naming: calling `runBlocking { }` inside `channelRead0` to use a suspend function. That blocks the event loop just like `Thread.sleep`. If you want coroutines, launch on a scope with its own dispatcher and call `ctx.writeAndFlush` from the coroutine, which is the same manual dispatch with a different executor."
 },
 "worked": {
  "title": "Offload a handler without racing on its state",
  "steps": [
   {"say": "A handler counts the authorizations it has served on each connection and calls a card issuer that takes 120 ms. It blocks the loop. The field `served` is safe only because one thread touches it.",
    "code": "final class AuthHandler extends SimpleChannelInboundHandler<AuthRequest> {\n    private int served;                                 // per-connection state\n\n    @Override\n    protected void channelRead0(ChannelHandlerContext ctx, AuthRequest req) {\n        AuthResponse res = issuer.authorize(req);       // 120 ms, on the event loop\n        served++;\n        ctx.writeAndFlush(res.withSequence(served));\n    }\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "class AuthHandler : SimpleChannelInboundHandler<AuthRequest>() {\n    private var served = 0                              // per-connection state\n\n    override fun channelRead0(ctx: ChannelHandlerContext, req: AuthRequest) {\n        val res = issuer.authorize(req)                 // 120 ms, on the event loop\n        served++\n        ctx.writeAndFlush(res.withSequence(served))\n    }\n}"},
   {"say": "Moving everything into the executor frees the loop but breaks the counter. Two requests on the same connection now run on two pool threads at once, and `served++` is a read-modify-write race on a plain field.",
    "code": "blockingPool.execute(() -> {\n    AuthResponse res = issuer.authorize(req);\n    served++;                                           // two pool threads, one field: lost updates\n    ctx.writeAndFlush(res.withSequence(served));\n});",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "blockingPool.execute {\n    val res = issuer.authorize(req)\n    served++                                            // two pool threads, one field: lost updates\n    ctx.writeAndFlush(res.withSequence(served))\n}"},
   {"say": "Do only the blocking call in the pool, then hop back to the channel's loop for everything that touches handler state. The loop is the lock.",
    "code": "@Override\nprotected void channelRead0(ChannelHandlerContext ctx, AuthRequest req) {\n    blockingPool.execute(() -> {\n        AuthResponse res = issuer.authorize(req);       // 1. block off the loop\n        ctx.executor().execute(() -> {                  // 2. back on the channel's loop\n            served++;                                   // 3. confined state, no lock needed\n            ctx.writeAndFlush(res.withSequence(served));\n        });\n    });\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "override fun channelRead0(ctx: ChannelHandlerContext, req: AuthRequest) {\n    blockingPool.execute {\n        val res = issuer.authorize(req)                 // 1. block off the loop\n        ctx.executor().execute {                        // 2. back on the channel's loop\n            served++                                    // 3. confined state, no lock needed\n            ctx.writeAndFlush(res.withSequence(served))\n        }\n    }\n}"},
   {"say": "One thing the loop no longer gives you is order. Two requests on one connection can finish in either order, so replies can overtake each other. Either carry a correlation id the client matches on (most payment protocols do), or keep one request in flight per connection by turning off auto-read until the reply is written. Lesson 4 shows `AUTO_READ`.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build a quote server on Netty 4.2 and keep its loop free",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/QuoteServer.kt"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l03.*'",
  "steps": [
   "Run the tests. All four fail with `NotImplementedError`.",
   "Write `QuotePipeline.handlers`: `LineBasedFrameDecoder(MAX_LINE)`, `StringDecoder(UTF_8)`, `StringEncoder(UTF_8)`, then `business`. Write `UpperCaseHandler.channelRead0`. The two `EmbeddedChannel` tests should now pass.",
   "Build `QuoteServer` as its KDoc describes: one-thread `MultiThreadIoEventLoopGroup` with `NioIoHandler.newFactory()`, a `ServerBootstrap` with `NioServerSocketChannel`, and a `ChannelInitializer` that adds `QuotePipeline.handlers(QuoteHandler(blocking, lookup))`. Run the tests: three pass, and the slow-lookup test reports an event-loop lag near a second.",
   "Fix `QuoteHandler`: run the lookup on `blocking` and call `ctx.writeAndFlush` from there. Run the tests until all four pass."
  ],
  "hints": [
   "`ch.pipeline().addLast(*QuotePipeline.handlers(...))` uses Kotlin's spread operator to pass the array as varargs.",
   "Create a new `QuoteHandler` inside `initChannel`. A handler without `@Sharable` may only sit in one pipeline, and the server has many channels.",
   "`bind(InetAddress.getLoopbackAddress(), 0)` picks a free port; `port()` reads it back from the channel.",
   "The test's lag probe is `server.group.next().submit(Callable { ... })`. With one loop in the group, `next()` is always that loop."
  ],
  "done_when": "All four tests in `QuoteServerTest` pass."
 },
 "drill": {
  "title": "Write a Netty 4.2 bootstrap from memory",
  "minutes": 5,
  "prompt": "Close the lab. Write the code that starts a Netty 4.2 echo server on port 9000 with one acceptor loop, the default number of worker loops, and a handler that echoes each message back. Which class replaces `NioEventLoopGroup`, and why doesn't the echo handler release the message?",
  "answer": {"lang": "java", "src": """EventLoopGroup boss = new MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory());
EventLoopGroup workers = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
Channel server = new ServerBootstrap()
        .group(boss, workers)
        .channel(NioServerSocketChannel.class)
        .childHandler(new ChannelInitializer<SocketChannel>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ch.pipeline().addLast(new ChannelInboundHandlerAdapter() {
                    @Override
                    public void channelRead(ChannelHandlerContext ctx, Object msg) {
                        ctx.writeAndFlush(msg);   // the write takes ownership and releases it once sent
                    }
                });
            }
        })
        .bind(9000).sync().channel();
// MultiThreadIoEventLoopGroup + NioIoHandler.newFactory() replaces NioEventLoopGroup.""",
             "alt": {"lang": "kotlin", "src": """val boss = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
val workers = MultiThreadIoEventLoopGroup(NioIoHandler.newFactory())
val server = ServerBootstrap()
    .group(boss, workers)
    .channel(NioServerSocketChannel::class.java)
    .childHandler(object : ChannelInitializer<SocketChannel>() {
        override fun initChannel(ch: SocketChannel) {
            ch.pipeline().addLast(object : ChannelInboundHandlerAdapter() {
                override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
                    ctx.writeAndFlush(msg)   // the write takes ownership and releases it once sent
                }
            })
        }
    })
    .bind(9000).sync().channel()
// MultiThreadIoEventLoopGroup + NioIoHandler.newFactory() replaces NioEventLoopGroup."""}}
 },
 "recap": [
  "An `EventLoop` is one thread with a selector and a task queue. A channel is registered with one loop for life, so its handlers never run concurrently.",
  "Netty 4.2 builds groups as `new MultiThreadIoEventLoopGroup(n, NioIoHandler.newFactory())`; `NioEventLoopGroup` and its cousins are deprecated. The default size is 2 × cores.",
  "Inbound events flow from head to tail through decoders to your handler. Writes flow toward the head through encoders, starting at the current handler when you use `ctx`.",
  "`EmbeddedChannel` runs a pipeline without a socket: `writeInbound`, `readOutbound` and `finish()` make handlers easy to test.",
  "Never block a handler. Dispatch the slow part to your own executor and call `ctx.writeAndFlush` from there; the per-handler `EventExecutorGroup` overloads are deprecated in 4.2."
 ],
 "quiz": [
  {"q": "A Netty server's worker group has 2 loops, and 6 clients connect one after another. Client 3's handler calls `Thread.sleep(500)`. Which clients are delayed?",
   "options": ["Only client 3", "Clients 1, 3 and 5, which share an event loop", "All 6 clients", "None: Netty gives each read its own thread"],
   "answer": 1,
   "why": "Channels are assigned round-robin and stay on their loop for life, so clients 1, 3 and 5 share one thread. While client 3's handler sleeps, the other two wait. Clients 2, 4 and 6 run on the other loop and are not affected."},
  {"q": "A pipeline is built with `addLast(frameDecoder, stringDecoder, handlerA, stringEncoder, handlerB)`. `handlerA` calls `ctx.writeAndFlush(\"ok\\n\")` with a `String`. What happens?",
   "options": ["The string is encoded and sent", "The write fails: `ctx` starts at handlerA and goes toward the head, so it never passes the encoder", "Netty reorders handlers so encoders always run last", "handlerB receives the string as an inbound message"],
   "answer": 1,
   "why": "`ctx.writeAndFlush` travels from handlerA toward the head, and the encoder sits on the other side of handlerA. The head only accepts `ByteBuf` and `FileRegion`, so the write future fails. `ctx.channel().writeAndFlush` would start at the tail and pass the encoder."},
  {"q": "What is the Netty 4.2 way to call a blocking JDBC query from a handler?",
   "options": ["`pipeline.addLast(new DefaultEventExecutorGroup(16), \"jdbc\", handler)`", "Call it directly: Netty 4.2 event loops are virtual threads", "Hand the query to your own executor and call `ctx.writeAndFlush` with the result from there", "Wrap the call in `synchronized` so only one loop blocks at a time"],
   "answer": 2,
   "why": "4.2 deprecated the per-handler executor overloads and recommends dispatching manually. Netty's loops are platform threads, and a `synchronized` block still blocks the thread that runs it."},
  {"q": "From lesson 2: Netty's NIO transport only asks the selector for `OP_WRITE` while a channel has bytes it couldn't write yet. Why?",
   "options": ["Linux selectors are level-triggered, so a socket with free send-buffer space would be reported on every select and the loop would spin", "OP_WRITE is slower than OP_READ", "Edge-triggered epoll would lose the event", "The JDK forbids registering OP_WRITE together with OP_READ"],
   "answer": 0,
   "why": "A socket is writable almost all the time. With level-triggered `epoll`, a permanent `OP_WRITE` makes every `select()` return at once. Netty sets it after an incomplete write and clears it when the outbound buffer drains, which is the rule from lesson 2.",
   "from": "io-02"},
  {"q": "A test writes `\"auth-1\\nauth-2\\n\"` in one `writeInbound` call into an `EmbeddedChannel` holding `LineBasedFrameDecoder`, `StringDecoder`, `StringEncoder` and a handler that replies once per line. How many messages does `readOutbound()` return?",
   "options": ["1", "0 until you call `finish()`", "It depends on how the network splits the bytes", "2"],
   "answer": 3,
   "why": "The frame decoder emits one frame per line, even when both lines arrive in one buffer, and the handler replies to each. `EmbeddedChannel` runs everything synchronously on the calling thread, with no network involved, so the answer is always 2."}
 ],
 "flashcards": [
  {"front": "Netty 4.2 replacement for `new NioEventLoopGroup()`?", "back": "`new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory())`, optionally with a thread count. The same pattern works with `EpollIoHandler`, `KQueueIoHandler` and `IoUringIoHandler`."},
  {"front": "Default number of event loops in a Netty group?", "back": "2 × available processors (property `io.netty.eventLoopThreads`): 8 on a 4-core machine."},
  {"front": "How long does a channel stay on its event loop?", "back": "For its whole life. All its events run on that one thread, one after another."},
  {"front": "`ctx.writeAndFlush(msg)` vs `ctx.channel().writeAndFlush(msg)`?", "back": "`ctx` starts at the current handler and goes toward the head. `channel()` starts at the tail and passes every outbound handler."},
  {"front": "Is `ctx.writeAndFlush` safe to call from a thread that isn't the event loop?", "back": "Yes. Netty sees `inEventLoop()` is false and queues the write as a task on the channel's own loop."},
  {"front": "Why did Netty 4.2 deprecate `addLast(EventExecutorGroup, ...)`?", "back": "Per-handler executors caused more problems than they solved. Netty now says to dispatch blocking work manually to your own executor."},
  {"front": "What is an event-loop lag probe?", "back": "Submit an empty task to the loop and time how long it waits to run. Near 0 ms on a healthy loop; about the block time when a handler blocks."}
 ],
 "terms": [
  {"term": "EventLoop", "plain": "One thread that runs a selector over its channels plus a queue of tasks."},
  {"term": "EventLoopGroup", "plain": "A set of event loops; new channels are spread over them round-robin."},
  {"term": "IoHandler", "plain": "Netty 4.2's transport-specific engine inside a loop: NIO, epoll, kqueue or io_uring."},
  {"term": "ChannelPipeline", "plain": "The ordered list of handlers every event and write of a channel passes through."},
  {"term": "Inbound handler", "plain": "A handler for events coming from the socket, such as `channelRead`."},
  {"term": "Outbound handler", "plain": "A handler for operations going to the socket, such as `write` and `flush`."},
  {"term": "EmbeddedChannel", "plain": "A channel with no socket, for testing a pipeline synchronously."}
 ],
 "explain_back": {
  "prompt": "Explain why a Netty handler that runs a 200 ms JDBC query slows down clients that never send that query, and how you would fix it in Netty 4.2.",
  "answer": "Each channel is registered with one event loop for its whole life, and a loop is a single thread that runs the handlers of all its channels one event at a time. While the handler waits 200 ms for JDBC, that thread can't read, decode or write for any other channel on the same loop, so their requests queue behind the query. The fix in 4.2 is manual dispatch: in the handler, hand the query to an application executor sized for blocking work (or virtual threads), and call `ctx.writeAndFlush` with the result from that executor. Netty queues the write back onto the channel's loop. If the code needs handler state, hop back with `ctx.executor().execute` first. The deprecated `addLast(EventExecutorGroup, ...)` is not the answer anymore."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two details make manual dispatch work, and both are worth reading in Netty's source.

First, every outbound call checks where it runs. `AbstractChannelHandlerContext.write` asks `executor.inEventLoop()`. On the loop, it calls the next handler directly. Off the loop, it wraps the write in a task and puts it on the loop's queue. That is why `ctx.writeAndFlush` from your pool is safe, and also why it is not free: each one is a task hand-off and a wake-up of the selector.

Second, the loop interleaves IO and tasks. A Netty 4.2 loop is a `SingleThreadIoEventLoop`: it runs the IO handler (select and process ready channels), then drains its task queue, then selects again. Tasks you submit from other threads, writes from your pool, and timers all share the thread with IO. The 4.2 migration guide mentions hooks to measure how long IO processing and task processing take per loop run, for exactly this kind of tuning.

When you dispatch, think about the order of replies on a connection, as the worked example showed, and about backpressure: if the pool is slower than the arrival rate, its queue grows without bound unless something stops reading. Lesson 4 covers `AUTO_READ` and writability, which are Netty's tools for that.

To catch accidental blocking in tests, Netty ships an integration for BlockHound (`Hidden$NettyBlockHoundIntegration` in `netty-common`). BlockHound itself is a separate Java agent library. Installed in a test, it throws when code on a Netty event-loop thread calls a known blocking method such as `Thread.sleep` or a socket read."""
 },
 "sources": [
  {"title": "Netty 4.2 Migration Guide (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md"},
  {"title": "MultiThreadIoEventLoopGroup source, Netty 4.2 branch", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/MultiThreadIoEventLoopGroup.java"},
  {"title": "ChannelPipeline source and Javadoc, Netty 4.2 branch", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/ChannelPipeline.java"},
  {"title": "Netty commit d64340b: deprecate the EventExecutorGroup overloads", "url": "https://github.com/netty/netty/commit/d64340b"}
 ]
}

out = ROOT / "content/lessons/io-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
