import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l01"
K = "kotlin/workbench/quotes/l01"
read = lambda p: (ROOT / p).read_text()


def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def demo(name, title_j=None):
    """A Try-it code object for a Java demo with its Kotlin twin."""
    return {
        "lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{J}/{name}.java"),
        "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l01.{name}",
        "file": f"{lab}/demo/{J}/{name}.java",
        "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l01.{name}Kt",
                "file": f"{lab}/demo/{K}/{name}.kt"},
    }


# ---- the figure: one loop, the pipeline, the source ----
row = [  # x, width, class, line1, line2
    (12, 76, "box", "client", "7 EURUSD"),
    (104, 104, "box", "frame", "max 64 bytes"),
    (220, 84, "box", "decode", "UTF-8"),
    (316, 84, "box-b", "encode", "replies out"),
    (412, 96, "box", "flow ctl", "holds lines"),
    (524, 124, "box-a", "QuoteHandler", "max 16 waiting"),
]
parts = []
for i, (x, w, cls, l1, l2) in enumerate(row):
    parts.append(f'<rect class="{cls}" x="{x}" y="50" width="{w}" height="52" rx="8"/>')
    parts.append(f'<text class="t" x="{x + w // 2}" y="72" text-anchor="middle">{l1}</text>')
    parts.append(f'<text class="t-s t-m" x="{x + w // 2}" y="92" text-anchor="middle">{l2}</text>')
    if i + 1 < len(row):
        nx = row[i + 1][0]
        parts.append(f'<line class="ln" x1="{x + w + 2}" y1="76" x2="{nx - 2}" y2="76" marker-end="url(#arr)"/>')
FIG = (
    '<svg viewBox="0 0 700 290" role="img" aria-label="The quote server: a client line passes the frame decoder, '
    'string decoder, string encoder and flow control handler to QuoteHandler, which asks QuoteSource for a future '
    'and gets the callback back on the same event loop. Auto-read is on only while the channel is writable and fewer '
    'than 16 requests wait. One event-loop thread runs all of it.">'
    '<text class="t-s t-a" x="330" y="34" text-anchor="middle">requests flow in, replies flow back out through the encoder</text>'
    + "".join(parts)
    + '<line class="ln-a" x1="566" y1="104" x2="566" y2="156" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="606" y1="158" x2="606" y2="106" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="536" y="134" text-anchor="middle">quote()</text>'
    '<text class="t-s t-a" x="644" y="128" text-anchor="middle">callback</text>'
    '<text class="t-s t-a" x="648" y="144" text-anchor="middle">on the loop</text>'
    '<rect class="box" x="524" y="160" width="124" height="52" rx="8"/>'
    '<text class="t" x="586" y="182" text-anchor="middle">QuoteSource</text>'
    '<text class="t-s t-m" x="586" y="202" text-anchor="middle">returns a future</text>'
    '<rect class="box-dim" x="104" y="160" width="404" height="52" rx="8"/>'
    '<text class="t-s" x="306" y="181" text-anchor="middle">auto-read is on only while the channel is writable</text>'
    '<text class="t-s" x="306" y="199" text-anchor="middle">and fewer than 16 requests are waiting</text>'
    '<rect class="box-ok" x="12" y="236" width="636" height="40" rx="8"/>'
    '<text class="t" x="330" y="261" text-anchor="middle">one event-loop thread runs every box above, and it never waits</text>'
    '</svg>'
)

J_PIPE = """ChannelHandler[] handlers(QuoteSource source) {
    return new ChannelHandler[] {
        new LineBasedFrameDecoder(64),        // one line per message; a longer line fails
        new StringDecoder(UTF_8),
        new StringEncoder(UTF_8),             // outbound: String to bytes
        new FlowControlHandler(),             // section 3 explains this one
        new QuoteHandler(source),             // new per connection: it keeps state
    };
}"""
K_PIPE = """fun handlers(source: QuoteSource): Array<ChannelHandler> = arrayOf(
    LineBasedFrameDecoder(64),                // one line per message; a longer line fails
    StringDecoder(UTF_8),
    StringEncoder(UTF_8),                     // outbound: String to bytes
    FlowControlHandler(),                     // section 3 explains this one
    QuoteHandler(source),                     // new per connection: it keeps state
)"""

J_JOIN = """@Override
protected void channelRead0(ChannelHandlerContext ctx, String line) {
    Request r = QuoteProtocol.parse(line);
    Quote q = source.quote(r.symbol()).join();          // the loop waits here
    ctx.writeAndFlush(QuoteProtocol.ok(r.id(), q));
}"""
K_JOIN = """override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    val r = QuoteProtocol.parse(line)
    val q = source.quote(r.symbol).join()               // the loop waits here
    ctx.writeAndFlush(QuoteProtocol.ok(r.id, q))
}"""

J_ASYNC = """CompletableFuture<Quote> quote = source.quote(r.symbol());   // 1. returns at once
inFlight.add(quote);
quote.whenCompleteAsync((q, e) -> {                           // 2. later, on this channel's loop
    inFlight.remove(quote);
    ctx.writeAndFlush(e == null ? ok(r.id(), q) : error(r.id(), e));
}, ctx.executor());"""
K_ASYNC = """val quote = source.quote(r.symbol)                            // 1. returns at once
inFlight += quote
quote.whenCompleteAsync({ q, e ->                             // 2. later, on this channel's loop
    inFlight -= quote
    ctx.writeAndFlush(if (e == null) ok(r.id, q) else error(r.id, e))
}, ctx.executor())"""

J_RULE = """private void updateReading(ChannelHandlerContext ctx) {
    boolean read = ctx.channel().isWritable() && inFlight.size() < MAX_IN_FLIGHT;
    ctx.channel().config().setAutoRead(read);
}"""
K_RULE = """private fun updateReading(ctx: ChannelHandlerContext) {
    val read = ctx.channel().isWritable && inFlight.size < MAX_IN_FLIGHT
    ctx.channel().config().isAutoRead = read
}"""

J_CLOSE = """@Override
public void close() {
    stopAccepting();                                    // 1. close the listening socket
    connections.close().syncUninterruptibly();          // 2. close every open connection
    group.shutdownGracefully(0, 2, TimeUnit.SECONDS)    // 3. then stop the loop threads
         .syncUninterruptibly();
}"""
K_CLOSE = """override fun close() {
    stopAccepting()                                     // 1. close the listening socket
    connections.close().syncUninterruptibly()           // 2. close every open connection
    group.shutdownGracefully(0, 2, TimeUnit.SECONDS)    // 3. then stop the loop threads
        .syncUninterruptibly()
}"""

S1 = f"""Over three lessons you build one program: a small quote service. A client opens a TCP connection and sends a line such as `7 EURUSD`. The service asks three FX providers for a price and answers `7 OK EURUSD 1.0842 northbank`, the best price it got, within 300 ms. The providers are invented (Northbank, Eastgate and Fjord), and like real ones they are slow on a bad day and sometimes down. This lesson builds the server shell on Netty. Lesson 2 of this track adds the fan-out to the providers with coroutines and a deadline. Lesson 3 makes the whole thing hold up under load.

One rule shapes every decision: **the event loop never waits**. As "Netty: the event loop and the channel pipeline" showed, a channel is registered with one loop for its whole life, and that loop is a single thread that runs the handlers of every channel it owns. If a handler waits 100 ms for a provider, every connection on that loop gets 100 ms of silence.

The protocol is lines of text. A client can be `nc` in a terminal, tests can write requests as strings, and `LineBasedFrameDecoder` does the framing. A binary protocol would use a length field instead, as "Netty in practice: codecs, flow control and leaks" did, and nothing else in the design would change. Two details are deliberate.

The decoder takes at most 64 bytes per line. Without a limit, a client that sends bytes and never a newline makes the decoder buffer forever. A longer line fails with `TooLongFrameException`.

Every request carries an id, and every reply repeats it. A reply leaves when its quote arrives, so a fast quote overtakes a slow one and replies come back out of order. The client matches them by id.

Here is the pipeline. Each connection gets new instances, because the handler keeps state for its connection:

{pair(J_PIPE, K_PIPE)}

`FlowControlHandler` looks out of place for now. Section 3 shows what goes wrong without it."""

S2 = f"""`QuoteSource.quote(symbol)` returns a `CompletableFuture<Quote>`. The first draft of the handler, which is the starting code of this lesson's lab, waits for it:

{pair(J_JOIN, K_JOIN)}

It answers correctly, and it passes a test with one client. This section's demo measures what it costs, with one event loop, ten clients and a provider that takes 100 ms. The tenth reply came after 1,072 ms, and the provider never saw more than one quote at a time. The loop asked for a quote, held its thread in `join()` until the answer came, and only then read the next request.

The fix gives the future back to the loop and finishes later:

{pair(J_ASYNC, K_ASYNC)}

`channelRead0` now returns in microseconds. The same demo answered all ten clients in 106 ms, with ten quotes waiting at once.

The second argument decides which thread runs the callback. `ctx.executor()` is the channel's own event loop, so the callback runs there as a task, like every other event of this channel. That matters because the handler keeps state, the set of in-flight futures. With plain `whenComplete`, the callback would run on whatever thread completed the future, a provider's thread, while the loop adds to the same `HashSet` in `channelRead0`. That is the read-modify-write race from "Race conditions: why count++ lies". When every touch of handler state happens on the loop, you need no lock: the loop is the lock. `ctx.writeAndFlush` would be safe from any thread. The set is not.

The interface carries the other half of the rule: `quote` must return at once and complete the future later. Lesson 2 meets that contract by starting a coroutine with `scope.future {{ }}`. A `runBlocking {{ }}` in its place would block the loop exactly like `join()`.

How do you prove the loop is free? The lab in "Netty: the event loop and the channel pipeline" timed a lag probe and asserted under 300 ms. That holds on a quiet laptop. On a build machine running eight builds on four cores, a healthy loop can miss 300 ms, and a broken handler can pass when the fake provider answers fast. This lab's test counts instead. It holds 100 quotes open, checks that the source saw 100 calls, then checks that the loop ran 50 empty tasks. A loop stuck in `join()` shows 1 call, on any machine and at any load. The 5-second limit in the test only decides how soon a failure is reported."""

S3 = f"""A client may pipeline: send 20,000 requests without waiting for a single reply. Two things then grow in the server's memory. Each request that waits for its quote is a future in the in-flight set. Each reply the client hasn't read yet sits in the channel's outbound buffer, because `writeAndFlush` never blocks ("Netty in practice: codecs, flow control and leaks"). Nothing limits either one.

Netty gives you one control: auto-read. While it is on, the loop reads the socket whenever bytes arrive. Turn it off and the loop stops reading that channel, the kernel's buffers fill, and TCP's window makes the client wait. The policy is one rule, applied after every new request, after every reply, and whenever writability changes:

{pair(J_RULE, K_RULE)}

The cap of 16 bounds the futures one connection can hold. The writability check bounds the outbound buffer: `isWritable()` turns false above the high water mark, 64 KiB by default.

There is a catch, and the demo shows it. Turning auto-read off stops the next socket read. It doesn't stop the lines the decoder already has. One read can bring 64 KB, a few thousand requests, and `LineBasedFrameDecoder` hands every one of them to the handler before the loop looks at auto-read again. `FlowControlHandler`, placed between the decoders and your handler, closes that gap. While auto-read is off it holds the decoded lines, and it releases them as reading resumes.

The demo pipelines 20,000 requests and reads nothing for 500 ms:

| Policy | Requests taken while the client read nothing | Peak outbound buffer |
|---|---|---|
| none | all 20,000 | 2,487,339 bytes |
| the auto-read rule | 2,993 | 694,144 bytes |
| the rule and `FlowControlHandler` | 1,217 | 67,596 bytes |

The last two rows came out the same on every run. The first one moves with the machine's load: on a busy machine the server's own loop choked on its growing queue and took fewer requests, but the queue still reached megabytes. The last peak is the 64 KiB high water mark (65,536 bytes) plus a few replies. Every client still got all 20,000 replies once it read them. The lab tests the cap directly: 40 pipelined requests against a source that holds every quote must produce exactly 16 calls."""

S4 = f"""A connection ends in one of four ways, and each has its own code path.

The client sends `QUIT`. The server writes `BYE` and closes from the write's future, with `ctx.writeAndFlush("BYE\\n").addListener(ChannelFutureListener.CLOSE)`. Closing right after `flush()` can drop bytes that are still in the outbound buffer; "Netty in practice: codecs, flow control and leaks" lost 57,344 bytes that way.

A line is too long. `LineBasedFrameDecoder` throws `TooLongFrameException`, and Netty passes it to the handler's `exceptionCaught`. The server answers `ERR line too long` and closes the same way. A client that sends 100 bytes where 64 are allowed is broken or hostile, and neither deserves a long conversation.

The client hangs up. `channelInactive` runs on the loop, and the handler cancels every future still in its set. For a plain `CompletableFuture` that interrupts nothing, as "CompletableFuture: errors, timeouts and fan-out" showed. It tells the source that nobody wants the answer any more. Lesson 2 turns that cancel into a coroutine cancel that reaches all three provider calls.

The server shuts down. The order matters:

{pair(J_CLOSE, K_CLOSE)}

`stopAccepting()` closes the listening socket first, so no new connection arrives while the rest shuts down. `connections` is a `ChannelGroup`: the server adds each new channel to it, and the group drops a channel again when it closes. Closing the group closes every open connection, each handler sees `channelInactive` and cancels its work, and only then does `shutdownGracefully` stop the loop threads. `shutdownGracefully` also closes the channels it still finds, but in this track's test runs that wasn't reliable: in about one run in three, a client still saw its connection open after the loops had stopped. Closing the connections yourself makes the order explicit. Lesson 3 of this track puts one more step between the first two lines: a short grace period in which quotes already in flight can still be answered.

Check yourself before the lab: a client has two requests pending when `close()` runs. What does it read from its socket, and what happens to the two futures? (It reads end of stream, because its channel was closed. Both futures are cancelled in `channelInactive`.)"""

# ---- worked example: the counting test ----
W1J = """final class FakeSource implements QuoteSource {
    private final List<CompletableFuture<Quote>> pending = new ArrayList<>();   // guarded by this
    private int calls;

    @Override
    public synchronized CompletableFuture<Quote> quote(String symbol) {
        calls++;                                   // 1. count every call that reaches the source
        CompletableFuture<Quote> f = new CompletableFuture<>();
        pending.add(f);                            // 2. hold it: a blocked loop stays blocked
        notifyAll();
        return f;
    }
}"""
W1K = """class FakeSource : QuoteSource {
    private val pending = mutableListOf<CompletableFuture<Quote>>()   // guarded by this
    private var calls = 0

    @Synchronized
    override fun quote(symbol: String): CompletableFuture<Quote> {
        calls++                                    // 1. count every call that reaches the source
        val f = CompletableFuture<Quote>()
        pending += f                               // 2. hold it: a blocked loop stays blocked
        (this as Object).notifyAll()
        return f
    }
}"""
W2J = """static int probe(EventLoopGroup group, int tasks) throws InterruptedException {
    CountDownLatch ran = new CountDownLatch(tasks);
    for (int i = 0; i < tasks; i++) group.next().execute(ran::countDown);   // 3. empty tasks
    ran.await(5, TimeUnit.SECONDS);              // bounds the failure, it is not the assertion
    return tasks - (int) ran.getCount();         // 4. the assertion is on this count
}"""
W2K = """fun probe(group: EventLoopGroup, tasks: Int): Int {
    val ran = CountDownLatch(tasks)
    repeat(tasks) { group.next().execute(ran::countDown) }   // 3. empty tasks
    ran.await(5, TimeUnit.SECONDS)               // bounds the failure, it is not the assertion
    return tasks - ran.count.toInt()             // 4. the assertion is on this count
}"""
W3J = """for (int c = 0; c < 10; c++) {                    // 10 connections x 10 requests
    Client client = new Client(server.port());
    clients.add(client);
    client.send(requests(c * 10, 10));
}
assertThat(source.awaitCalls(100)).isEqualTo(100);           // 5. the loop asked for all 100
assertThat(probe(server.group(), 50)).isEqualTo(50);         // 6. and still ran other work
source.releaseAll();
for (int c = 0; c < 10; c++) assertThat(clients.get(c).readIds(10)).isEqualTo(ids(c * 10, 10));"""
W3K = """val clients = List(10) { c ->                     // 10 connections x 10 requests
    Client(server.port()).also { it.send(requests(c * 10, 10)) }
}
assertThat(source.awaitCalls(100)).isEqualTo(100)            // 5. the loop asked for all 100
assertThat(probe(server.group(), 50)).isEqualTo(50)          // 6. and still ran other work
source.releaseAll()
clients.forEachIndexed { c, client -> assertThat(client.readIds(10)).isEqualTo(ids(c * 10, 10)) }"""

COMPARE_J = """@Override
protected void channelRead0(ChannelHandlerContext ctx, String line) {
    QuoteProtocol.Request r = QuoteProtocol.parse(line);
    CompletableFuture<Quote> quote = source.quote(r.symbol());
    inFlight.add(quote);
    updateReading(ctx);
    quote.whenCompleteAsync((q, e) -> {
        inFlight.remove(quote);
        if (ctx.channel().isActive()) {
            ctx.writeAndFlush(e == null ? QuoteProtocol.ok(r.id(), q) : QuoteProtocol.error(r.id(), e));
        }
        updateReading(ctx);
    }, ctx.executor());
}

@Override
public void channelInactive(ChannelHandlerContext ctx) {
    for (CompletableFuture<Quote> f : List.copyOf(inFlight)) f.cancel(true);
    inFlight.clear();
    ctx.fireChannelInactive();
}"""
COMPARE_K = """override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    val r = QuoteProtocol.parse(line)
    val quote = source.quote(r.symbol)
    inFlight += quote
    updateReading(ctx)
    quote.whenCompleteAsync({ q: Quote?, e: Throwable? ->     // platform types: say they can be null
        inFlight -= quote
        if (ctx.channel().isActive) {
            ctx.writeAndFlush(if (e == null) QuoteProtocol.ok(r.id, q) else QuoteProtocol.error(r.id, e))
        }
        updateReading(ctx)
    }, ctx.executor())
}

override fun channelInactive(ctx: ChannelHandlerContext) {
    inFlight.toList().forEach { it.cancel(true) }
    inFlight.clear()
    ctx.fireChannelInactive()
}"""

DRILL_J = """@Override
protected void channelRead0(ChannelHandlerContext ctx, String line) {
    Request r = QuoteProtocol.parse(line);
    CompletableFuture<Quote> quote = source.quote(r.symbol());   // returns at once
    inFlight.add(quote);
    updateReading(ctx);
    quote.whenCompleteAsync((q, e) -> {                           // runs on this channel's loop
        inFlight.remove(quote);
        if (ctx.channel().isActive()) ctx.writeAndFlush(e == null ? ok(r.id(), q) : error(r.id(), e));
        updateReading(ctx);
    }, ctx.executor());
}

// the rule: read only while writable and under the cap
// setAutoRead(ctx.channel().isWritable() && inFlight.size() < MAX_IN_FLIGHT)"""
DRILL_K = """override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    val r = QuoteProtocol.parse(line)
    val quote = source.quote(r.symbol)                            // returns at once
    inFlight += quote
    updateReading(ctx)
    quote.whenCompleteAsync({ q, e ->                             // runs on this channel's loop
        inFlight -= quote
        if (ctx.channel().isActive) ctx.writeAndFlush(if (e == null) ok(r.id, q) else error(r.id, e))
        updateReading(ctx)
    }, ctx.executor())
}

// the rule: read only while writable and under the cap
// isAutoRead = ctx.channel().isWritable && inFlight.size < MAX_IN_FLIGHT"""

L = {
 "id": "cap2-01",
 "title": "A Netty server that never blocks its loop",
 "minutes": 38,
 "goal": "By the end you can build the shell of a non-blocking quote server on Netty 4.2 (a line protocol with request ids and a length limit, a handler that never waits on its event loop, reading that pauses when a client stops reading, and a clean close) and prove that the loop stays free with a test that counts instead of timing.",
 "warmup": {
  "q": "A Netty server has one event loop. Its handler calls `source.quote(symbol).join()`, and each quote takes 100 ms. Ten clients send one request each at the same moment. When does the last client get its reply?",
  "options": [
   "After about 100 ms: the ten quotes wait at the same time",
   "After about 1 second: the loop waits for each quote in turn",
   "After about 200 ms: Netty starts a second loop when the first one is busy",
   "Never: Netty throws when a handler calls `join()`"
  ],
  "answer": 1,
  "why": "The loop is one thread, and `join()` holds it for the whole 100 ms. It reads the next request only after the current quote is back, so the ten quotes run one after another: about 1,000 ms (1,072 ms in this lesson's demo). Netty never adds loops on its own and doesn't detect blocking. Handing the future back lets all ten wait at once, and the same demo then answers everyone in about 100 ms."
 },
 "sections": [
  {
   "h": "The service we are building, and the rule it never breaks",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One event loop carries every request through the pipeline. The handler asks the source for a future and gets the callback back on the same loop, and auto-read decides when it takes the next line."},
   "try": {
    "title": "Feed the pipeline by hand",
    "minutes": 4,
    "steps": [
     "Open `ProtocolDemo.java` (or `ProtocolDemo.kt`). It pushes bytes into a line pipeline with `EmbeddedChannel` and completes the two quotes by hand, GBPUSD first.",
     "Predict what comes out after each of the five steps, and whether the channel is still open at the end.",
     "Run it. Then run it again with `-Pargs=6`, a 6-byte line limit. Predict first: `7 EURUSD` is 8 bytes."
    ],
    "code": demo("ProtocolDemo"),
    "expect": "Half a line produces nothing. The second write completes both requests, but nothing comes out until a price arrives. GBPUSD answers first, so `8 OK GBPUSD 1.2710 fjord` leaves before `7 OK EURUSD 1.0842 northbank`: the ids are what let a client match them. The 100-byte line gets `ERR line too long` and the channel closes. With a 6-byte limit, the second write already fails: `7 EURUSD` is too long, the channel closes, and the later steps find nothing to do."
   },
   "refs": [
    {"title": "LineBasedFrameDecoder source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/codec-base/src/main/java/io/netty/handler/codec/LineBasedFrameDecoder.java", "kind": "docs"}
   ]
  },
  {
   "h": "Hand the future back instead of waiting for it",
   "body": S2,
   "try": {
    "title": "Ten clients, one loop, two handlers",
    "minutes": 4,
    "steps": [
     "Open `BlockedLoopDemo.java` (or the Kotlin twin). One event loop serves ten clients; the provider answers each quote after 100 ms.",
     "Predict the time until all ten replies, and the most quotes waiting at the same time, for `join` and for `async`.",
     "Run it. Then change the group to `new MultiThreadIoEventLoopGroup(2, ...)` and predict the `join` numbers again."
    ],
    "code": demo("BlockedLoopDemo"),
    "expect": "`join`: about 1,070 ms and 1 quote at a time, because the loop waits for each quote before it reads the next request. `async`: about 105 ms and 10 at once. With two loops, the ten connections are split five and five, so `join` takes about 500 ms with 2 quotes at a time: more threads divide the damage, they don't remove it."
   },
   "refs": [
    {"title": "CompletableFuture (Java SE 25 API): whenCompleteAsync", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html", "kind": "docs"}
   ]
  },
  {
   "h": "Auto-read is the only tap you control",
   "body": S3,
   "try": {
    "title": "Pipeline 20,000 requests at a client that doesn't read",
    "minutes": 5,
    "steps": [
     "Open `BackpressureDemo.java` (or the Kotlin twin). It runs the same server three times: no policy, the auto-read rule, and the rule plus `FlowControlHandler`.",
     "Run it and compare the three lines.",
     "Change `MAX_IN_FLIGHT` to 1. Predict the third line: does the peak change much, and do all 20,000 replies still arrive?"
    ],
    "code": demo("BackpressureDemo"),
    "expect": "No policy: the server takes everything the client manages to send, all 20,000 on a quiet machine, and queues 1 to 2.5 MB of replies; this row changes from run to run. The rule alone: about 3,000 requests and 690 KB, because one read brought thousands of lines and the decoder delivered them all. With `FlowControlHandler`: about 1,200 requests and about 67,600 bytes, just above the 64 KiB high water mark. With a cap of 1 the peak stays near the high water mark (writability is what stops it) and every reply still arrives, more slowly, one request at a time."
   },
   "refs": [
    {"title": "FlowControlHandler source and Javadoc, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/handler/src/main/java/io/netty/handler/flow/FlowControlHandler.java", "kind": "docs"}
   ]
  },
  {
   "h": "Close on purpose: say why, cancel what nobody will read, then stop",
   "body": S4,
   "refs": [
    {"title": "WriteBufferWaterMark source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/WriteBufferWaterMark.java", "kind": "docs"}
   ]
  }
 ],
 "analogy": "One waiter covers a section of tables, as one event loop covers its channels. The first-draft handler is a waiter who takes an order, walks to the kitchen and stands at the pass until the dish is ready, while every other table in the section waits. The fixed handler leaves the ticket with the kitchen and walks on, and when the bell rings for that ticket, the same waiter carries the plate (`whenCompleteAsync` on the channel's own loop). The auto-read rule is the waiter taking no new orders from a table that already has 16 dishes coming or hasn't cleared its last plates, and `FlowControlHandler` keeps the order slips already written in the waiter's pocket. The analogy breaks at the kitchen door: a real waiter can see that the kitchen is slow. The loop knows only what your handler counts.",
 "in_your_world": "Every Quarkus REST endpoint that returns a `Uni` runs on a Vert.x event loop, and a Vert.x event loop is a Netty event loop (\"Quarkus on Vert.x: IO threads, workers and virtual threads\"). A `.await().indefinitely()` inside such an endpoint is this lesson's `join()`: it stalls every request on that loop, not just its own. The same server shape appears wherever payments meet long-lived TCP. An acquirer link that carries many authorizations on one connection matches replies by a trace number, for the same reason this protocol has an id, and a terminal that bursts its queued requests after a network blip is a pipelining client. Give such a link the same three guards: a frame limit, a cap on requests in flight per connection, and reading that follows writability.",
 "mistake": "The most common mistake is blocking the event loop \"just a little\": `join()`, `get()`, `block()` or `runBlocking` in a handler, because the provider usually answers in 5 ms. It passes every test with one client and a fast fake. Under load, 5 ms per request on a loop that serves 2,000 connections is a queue that never drains, and a provider that stalls for 2 seconds freezes every connection on that loop. The runner-up is the half fix: `whenComplete` instead of `whenCompleteAsync(..., ctx.executor())`. It frees the loop but lets provider threads touch the handler's state. Return the future from `channelRead0`, and finish on the channel's own loop.",
 "compare": {
  "title": "The non-blocking handler in Java and Kotlin",
  "java": {"title": "QuoteHandler.java (core)", "src": COMPARE_J},
  "kotlin": {"title": "QuoteHandler.kt (core)", "src": COMPARE_K},
  "note": "At runtime these are the same handler: Netty sees a `SimpleChannelInboundHandler<String>`, and the Kotlin lambda becomes a `BiConsumer` through SAM conversion. One Kotlin detail needs care. `whenCompleteAsync` comes from Java, so `q` and `e` arrive as platform types, and Kotlin won't stop you calling `q.price` when the future failed and `q` is null. Declare them `Quote?` and `Throwable?` so the compiler makes you check. Kotlin also tempts you with one thing Java doesn't have: `runBlocking { }` around a suspend call inside `channelRead0`. It blocks the loop exactly like `join()`. Lesson 2 of this track shows the bridge that doesn't: `scope.future { }`, which returns at once."
 },
 "worked": {
  "title": "Write the test that proves the loop is free, by counting",
  "steps": [
   {"say": "Decide what to count. Hold every quote open, so a blocked loop stays blocked for the whole test, and count something the loop can only do while it is free: calls that reach the source. The fake keeps each future until the test releases it.",
    "code": W1J, "lang": "java", "alt_code": W1K, "alt_lang": "kotlin"},
   {"say": "Add a probe: hand the loop empty tasks and count how many ran. The 5-second wait only bounds how long a failure takes to report. The assertion is on the count, so a slow machine can't fail a healthy loop.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Spread 100 requests over 10 connections. One connection may hold only 16 requests (section 3), so 100 on one connection would test the cap instead of the loop. Assert both counts, then release the quotes and check that every id came back on the right connection.",
    "code": W3J, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"},
   {"say": "Release the quotes in `finally`. A broken handler is stuck in `join()`; completing its future wakes the loop, so the server can close and the next test starts clean. Self-check: against the first-draft handler, which assertion fails, and with what number? (The first one: `expected: 100 but was: 1`. The loop took one request and has been waiting in `join()` ever since.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build the server shell and keep its loop free",
  "minutes": 15,
  "files": [
   f"{lab}/main/{J}/QuotePipeline.java",
   f"{lab}/main/{J}/QuoteHandler.java",
   f"{lab}/main/{J}/QuoteServer.java",
   f"{lab}/main/{J}/QuoteProtocol.java",
   f"{lab}/main/{J}/QuoteSource.java",
   f"{lab}/main/{J}/Quote.java"
  ],
  "run": "./gradlew :quotes:test --tests 'workbench.quotes.l01.*'",
  "steps": [
   "Run the tests. All eight fail. Read `QuoteProtocol.java` (the wire format) and `QuoteSource.java` (the contract: return at once). The tests' fake source is in `src/test/.../l01/FakeSource.java`.",
   "Write `QuotePipeline.handlers`: the five handlers in the order its Javadoc lists. The framing and `QUIT` tests should pass now.",
   "Fix point 1 in `QuoteHandler`: add a `Set<CompletableFuture<Quote>> inFlight` field, keep each future in it, and write the reply in `whenCompleteAsync(..., ctx.executor())`. Skip the write if the channel is no longer active.",
   "Add `updateReading` (point 2) and call it after adding a future, after each reply, and in `channelWritabilityChanged`.",
   "Cancel the in-flight futures in `channelInactive` (point 3), and answer a too-long line in `exceptionCaught` (point 4).",
   "Write `QuoteServer.close()` in the order its Javadoc gives. Run the tests until all eight pass, then run them twice more."
  ],
  "hints": [
   "If the 100-pending test says `expected: 100 but was: 1`, the loop is still inside `join()` somewhere in `channelRead0`.",
   "If the `MAX_IN_FLIGHT` test sees more than 16 calls, check that `FlowControlHandler` sits between the decoders and `QuoteHandler`, and that you call `updateReading` right after adding the future.",
   "`whenCompleteAsync` runs the callback as a task on the loop. In the `EmbeddedChannel` tests the replies appear after `runPendingTasks()`, which the tests call for you.",
   "`exceptionCaught` receives the `TooLongFrameException` itself. `QUIT` shows the close: `ctx.writeAndFlush(...).addListener(ChannelFutureListener.CLOSE)`."
  ],
  "done_when": "All eight tests in `QuoteServerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the non-blocking reply from memory",
  "minutes": 4,
  "prompt": "Close the lab. In a `SimpleChannelInboundHandler<String>` with a `QuoteSource source` and a `Set` called `inFlight`, write `channelRead0` so that it asks for the quote, keeps the future while it is pending, and writes the reply on the channel's own event loop. Then write the auto-read rule as one line. Which argument decides the thread that runs your callback?",
  "answer": {"lang": "java", "src": DRILL_J, "alt": {"lang": "kotlin", "src": DRILL_K}}
 },
 "recap": [
  "The program is a TCP quote service. This lesson is its Netty shell: a line protocol with request ids, a 64-byte line limit, and a `QuoteSource` that returns a future.",
  "The event loop never waits. `join()`, `get()` or `runBlocking` in a handler stalls every channel on that loop; hand the future back and finish in `whenCompleteAsync(..., ctx.executor())`, which keeps handler state on one thread.",
  "Prove it by counting: hold quotes open and count calls and probe tasks. A blocked loop shows 1 call whatever the machine's speed; a millisecond bar can fail a healthy loop on a busy box.",
  "Auto-read is the only tap: read while the channel is writable and fewer than 16 requests wait. `FlowControlHandler` holds lines already decoded, which took the demo's peak from 694,144 to 67,596 bytes.",
  "Close on purpose: `BYE` and errors close from the write's future, a hang-up cancels the in-flight futures, and the server stops accepting, closes its connections, and only then shuts its loops down."
 ],
 "quiz": [
  {
   "q": "The server runs 8 event loops with 800 connections, and the first-draft handler calls `source.quote(s).join()`. One provider stalls for 2 seconds on a single request. Who waits?",
   "options": [
    "Only the client whose quote stalled",
    "All 800 clients: Netty runs one handler at a time for the whole server",
    "About 100 clients: every connection registered on the same loop as that request",
    "Nobody: `join()` parks the loop thread and Netty moves its channels to another loop"
   ],
   "answer": 2,
   "why": "Channels are spread over the 8 loops round-robin and stay where they were registered, about 100 per loop. The loop running `join()` can't read, decode or write for any of its channels for 2 seconds, while the other 7 loops carry on. Netty never moves a channel to another loop.",
   "from": "io-03"
  },
  {
   "q": "A handler writes every reply with `ctx.writeAndFlush` and never looks at writability. A client pipelines thousands of requests and reads its socket slowly. Where do the unread replies pile up?",
   "options": [
    "In the client's receive buffer, which grows to fit",
    "Nowhere: `writeAndFlush` blocks the loop until the client reads",
    "In the kernel's send buffer, without limit",
    "In the channel's outbound buffer, in the server's own memory"
   ],
   "answer": 3,
   "why": "`writeAndFlush` never blocks. The kernel's buffers are small and fill first; after that Netty keeps the bytes in the channel's outbound buffer, in your heap or direct memory. In this lesson's demo that reached 2,487,339 bytes. Only reading less from that client stops it growing.",
   "from": "io-04"
  },
  {
   "q": "`QuoteHandler` finishes each quote with `whenCompleteAsync(callback, ctx.executor())`. What goes wrong with plain `whenComplete(callback)`?",
   "options": [
    "The callback runs on the thread that completed the future, so it races the event loop on the in-flight `HashSet`",
    "`writeAndFlush` throws, because it may only be called on the event loop",
    "Nothing: the two behave the same",
    "The callback never runs, because the loop doesn't know about it"
   ],
   "answer": 0,
   "why": "`whenComplete` runs the callback on whichever thread completes the future, here a provider's thread, while the loop adds to the same set in `channelRead0`: a read-modify-write race on a plain `HashSet`. `writeAndFlush` itself is safe from any thread, which is why the bug is easy to miss."
  },
  {
   "q": "In Reactive Streams a subscriber paces the publisher with `request(n)`. What plays that part between this server and one client?",
   "options": [
    "The 64-byte line limit",
    "Auto-read, switched on only while the channel is writable and fewer than 16 requests wait",
    "TCP's receive window on its own, with no code in the server",
    "The 64 KiB high water mark on its own"
   ],
   "answer": 1,
   "why": "Auto-read is the server's demand signal: it reads more only when it has room, and TCP carries the pause back to the client. TCP alone does nothing while the server keeps reading, because the bytes just move from the kernel into the server's heap. The water mark only reports a full buffer; your handler has to act on it.",
   "from": "rx-01"
  },
  {
   "q": "When a client hangs up, `channelInactive` calls `cancel(true)` on a pending future from a source that runs blocking calls with `supplyAsync` on a thread pool. What happens to the provider call?",
   "options": [
    "It is interrupted and stops at once",
    "The pool thread is stopped",
    "It runs to the end, and its result is dropped: `cancel` only completes the future",
    "The cancel fails, because the work has already started"
   ],
   "answer": 2,
   "why": "`CompletableFuture.cancel` completes the future with a `CancellationException` and doesn't interrupt the thread doing the work, whatever you pass. The call finishes and its result goes nowhere. To stop the work itself, the source has to react to the cancel, which is what lesson 2's coroutines do.",
   "from": "exec-07"
  }
 ],
 "flashcards": [
  {"front": "What does `join()` in a Netty handler cost?", "back": "Every channel on that event loop waits until the future completes, not just the one that asked."},
  {"front": "Why finish with `whenCompleteAsync(callback, ctx.executor())`?", "back": "The callback runs on the channel's own event loop, so the handler's state is only ever touched by one thread."},
  {"front": "When should the quote server read a connection?", "back": "Only while the channel is writable and fewer than `MAX_IN_FLIGHT` (16) of its requests are waiting for a quote."},
  {"front": "What does `FlowControlHandler` add when auto-read is off?", "back": "It holds messages the decoder already produced and releases them as reading resumes. Auto-read alone only stops the next socket read."},
  {"front": "Why count instead of time in a test that proves the loop is free?", "back": "A healthy loop can miss a millisecond bar on a busy machine. A blocked loop's count (1 call, 0 probe tasks) doesn't depend on speed."},
  {"front": "Why does the quote protocol carry a request id?", "back": "A reply leaves when its quote arrives, so replies can overtake each other. The client matches them by id."},
  {"front": "In what order does the server shut down?", "back": "Stop accepting, close every open connection (a `ChannelGroup`; handlers cancel their in-flight work), then `shutdownGracefully` to stop the loop threads."}
 ],
 "terms": [
  {"term": "Event loop", "plain": "One thread that reads, decodes and writes for every channel registered with it, plus a queue of tasks."},
  {"term": "Pipelining", "plain": "A client sends many requests without waiting for the replies."},
  {"term": "In-flight request", "plain": "A request the server has read but not yet answered."},
  {"term": "Auto-read", "plain": "Whether the loop keeps reading a channel's socket. Off means the kernel's buffers fill and TCP makes the client wait."},
  {"term": "FlowControlHandler", "plain": "A Netty handler that holds already-decoded messages while auto-read is off."},
  {"term": "Correlation id", "plain": "An id the client puts on a request and the server repeats on the reply, so replies can arrive in any order."},
  {"term": "Probe task", "plain": "An empty task handed to an event loop to check that it still runs work."}
 ],
 "explain_back": {
  "prompt": "A colleague reviews your handler: \"Why all this ceremony? The providers answer in 5 ms, so `join()` is fine, and Netty buffers writes for us anyway.\" Explain what `join()` costs on an event loop, why the callback runs on `ctx.executor()`, and why the server needs the auto-read rule.",
  "answer": "An event loop is one thread that serves every channel registered with it, so `join()` doesn't cost 5 ms for one client, it costs 5 ms for every client on that loop, on every request. Under load that is a queue that never drains, and when a provider stalls for two seconds, every connection on the loop freezes for two seconds. Handing the future back lets the loop keep reading and writing while any number of quotes wait. The callback runs on `ctx.executor()` so that the handler's state, the set of in-flight futures, is only touched by the loop thread; with plain `whenComplete` a provider thread would race the loop on that set. Netty does buffer writes, but without limit: a client that pipelines and doesn't read makes the outbound buffer and the set of pending futures grow in our memory. Auto-read is the one control we have, so we read only while the channel is writable and fewer than 16 requests wait, with `FlowControlHandler` holding lines the decoder already produced. In the demo that kept the peak at about 67 KB instead of 2.5 MB."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three things a production shell adds to this one.\n\nAn idle timeout. A client that connects and never sends a line holds a channel forever. `IdleStateHandler` fires an `IdleStateEvent` through `userEventTriggered` after a connection has been quiet for the time you set; close the channel there.\n\nTLS. An `SslHandler` goes first in the pipeline, before the frame decoder, and nothing after it changes. That is the payoff of keeping every concern in its own handler.\n\nLoop metrics. Every loop of a `MultiThreadIoEventLoopGroup` is a `SingleThreadEventExecutor`, and `pendingTasks()` is the length of its task queue. In this server every reply is a task, so a queue that keeps growing is a loop that can't keep up. Export it per loop.\n\nTwo limits of this lesson's design are worth knowing. The cap of 16 protects the server from one greedy client and does nothing against ten thousand polite ones: lesson 3 of this track adds a global admission limit that sheds load with a clear error. And `whenCompleteAsync` costs a task hand-off per reply even when the quote is already done. That is cheap next to a network round trip, and it buys the single-threaded handler state.\n\nFinally, the counting probe has a stronger cousin for tests: BlockHound, a separate Java agent library, throws as soon as code on a Netty event-loop thread calls a known blocking method such as `CompletableFuture.join` or `Thread.sleep`. Netty ships the integration for it (`Hidden$NettyBlockHoundIntegration` in `netty-common`)."
 },
 "sources": [
  {"title": "Netty 4.2 Migration Guide (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md"},
  {"title": "FlowControlHandler source and Javadoc, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/handler/src/main/java/io/netty/handler/flow/FlowControlHandler.java"},
  {"title": "ChannelConfig source (setAutoRead), Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/ChannelConfig.java"},
  {"title": "WriteBufferWaterMark source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/WriteBufferWaterMark.java"},
  {"title": "CompletableFuture (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html"}
 ]
}

out = ROOT / "content/lessons/cap2-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
