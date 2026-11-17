import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l01"
K = "kotlin/workbench/quotes/l01"
read = lambda p: (ROOT / p).read_text()


def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def fill(text, **parts):
    """Put code pairs into prose written with @@NAME@@ placeholders (no brace escaping needed)."""
    for k, v in parts.items():
        text = text.replace(f"@@{k}@@", v)
    assert "@@" not in text, text[text.index("@@") - 40:text.index("@@") + 40]
    return text


def demo(name):
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
    (12, 76, "box", "client", "7 LISBON"),
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
    '<svg viewBox="0 0 700 290" role="img" aria-label="The quote server: a request line from a client passes the frame decoder, '
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
        new LineBasedFrameDecoder(64),        // 1. bytes in, one line out; a longer line fails
        new StringDecoder(UTF_8),             // 2. line bytes to String
        new StringEncoder(UTF_8),             // 3. outbound: String to bytes
        new FlowControlHandler(),             // 4. section 3 explains this one
        new QuoteHandler(source),             // 5. new per connection: it keeps state
    };
}"""
K_PIPE = """fun handlers(source: QuoteSource): Array<ChannelHandler> = arrayOf(
    LineBasedFrameDecoder(64),                // 1. bytes in, one line out; a longer line fails
    StringDecoder(UTF_8),                     // 2. line bytes to String
    StringEncoder(UTF_8),                     // 3. outbound: String to bytes
    FlowControlHandler(),                     // 4. section 3 explains this one
    QuoteHandler(source),                     // 5. new per connection: it keeps state
)"""

J_JOIN = """// Naive: this will not work under load
@Override
protected void channelRead0(ChannelHandlerContext ctx, String line) {
    Request r = QuoteProtocol.parse(line);
    Quote q = source.quote(r.destination()).join();        // the loop waits here
    ctx.writeAndFlush(QuoteProtocol.ok(r.id(), q));
}"""
K_JOIN = """// Naive: this will not work under load
override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    val r = QuoteProtocol.parse(line)
    val q = source.quote(r.destination).join()             // the loop waits here
    ctx.writeAndFlush(QuoteProtocol.ok(r.id, q))
}"""

J_ASYNC = """CompletableFuture<Quote> quote = source.quote(r.destination());   // 1. returns at once
inFlight.add(quote);
quote.whenCompleteAsync((q, e) -> {                               // 2. later, on this channel's loop
    inFlight.remove(quote);
    ctx.writeAndFlush(e == null ? ok(r.id(), q) : error(r.id(), e));
}, ctx.executor());"""
K_ASYNC = """val quote = source.quote(r.destination)                          // 1. returns at once
inFlight += quote
quote.whenCompleteAsync({ q, e ->                                 // 2. later, on this channel's loop
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

OPENING = """Picture the counter of the post office from the Servers track, with a new job. A customer asks: "How much to send this parcel to Lisbon?" The post office doesn't carry parcels that far. It asks three courier companies, Northline, Eastgate and Fjord, and tells the customer the cheapest price within a third of a second. That's a quote service: a program that gives a price for a job before anyone books it.

The trap hides in the first line of code. The clerk holding the question needs a price, and the price is a phone call away. Make the call from the counter, and every customer in that clerk's row waits too. It passes every test with one customer, which is exactly how many customers a simple test has.

Zero-copy, epoll, io_uring, and choosing a server model ended the Servers track with a promise: a server whose loop never waits. In this lesson, we'll build that server's shell on Netty: a small protocol, a handler that hands the wait back, a tap that stops reading a customer who stops listening, and a clean close. Before we start, make a guess, and keep it in mind."""

S1 = fill("""Over three sittings, we'll build one program: the quote service from the opening. A server is a program that waits for other programs to connect and ask it things, and those other programs are its clients. A client opens a TCP connection, a two-way line between two programs over a network, and sends one line of text. The server answers with one line:

```text
client: 7 LISBON
server: 7 OK LISBON 12.42 northline
```

Read the reply aloud: request 7 went fine, sending the parcel to Lisbon costs 12.42, and Northline offered that price. The 7 is the client's own number for its question, a request id, and the server repeats it on the answer. We'll see in a moment why the client needs it. The three couriers are invented, and like real ones, they're slow on a bad day and sometimes don't answer at all.

The three sittings build the program from the outside in, and each one leans on a track of Part 2. This sitting builds the counter on Netty, the Java library for network servers from the Servers track. The next sitting asks the three couriers at once with Kotlin coroutines, the way the home cook from the coroutines track texted three shops. The last sitting keeps the service standing when a crowd arrives, with the slips of the Reactive track, the shelf of the Flow track and the limits of Part 1. Whenever we lean on an earlier lesson, we'll name it.

One rule shapes every decision: **the event loop never waits.** Netty: the event loop and the channel pipeline pictured Netty as a post office. Each clerk owns a row of mailboxes for good, and one house rule matters more than the rest: a clerk never stops to make a phone call. In Netty's words, the clerk is an **event loop**, one thread that serves many connections in turn, and each box is a **channel**, Netty's object for one open connection. If the code for one channel waits 100 ms for a courier, every channel in that row gets 100 ms of silence.

The protocol, the agreed shape of the messages, is lines of text. A client can be `nc`, a small terminal tool that opens a TCP connection and sends what you type, and tests can write requests as plain strings. A binary protocol would carry a length field instead, as Netty in practice: codecs, flow control and leaks did with its page count on the envelope, and nothing else in the design would change. Two details are there on purpose.

The server reads at most 64 bytes per line. Without a limit, a client that sends bytes and never a newline would make the server keep them all, waiting for a line that never ends. A longer line fails with `TooLongFrameException`.

Every request carries an id, and every reply repeats it. A reply leaves when its price arrives, so a quick answer overtakes a slow one, and replies come back out of order. The client matches them by id, the way you match a ticket stub to a coat.

Here's the pipeline, the line of stations that every message on a channel passes through. Each station is a handler, a small object that reacts to the channel's events. Each connection gets new instances, because the last handler keeps state for its own connection:

@@PIPE@@

Let's walk it in order. The frame decoder cuts the stream of bytes into lines (1), and the string decoder turns each line into a `String` (2). Replies travel the other way, through the encoder, which turns a `String` back into bytes (3). `FlowControlHandler` (4) looks out of place for now; section 3 shows what goes wrong without it. Finally, `QuoteHandler` (5) answers the request, and it is where the phone call hides.""", PIPE=pair(J_PIPE, K_PIPE))

S2 = fill("""The handler gets its prices from a `QuoteSource`. `QuoteSource.quote(destination)` returns a `CompletableFuture<Quote>`, the JDK's ticket for an answer that will come later. Coroutines meet Java pictured it as the neighbour's ticket: "come back with this, and the pie will be ready." The first draft of the handler, which is the starting code of this lesson's lab, takes the ticket and waits at the neighbour's door:

@@JOIN@@

`join()` waits until the future has its answer, and it holds the thread while it waits. The draft answers correctly, and it passes a test with one client. This section's demo measures what it costs, with one event loop, ten clients, and a courier that needs 100 ms per price. One run on the busy machine used for this course printed:

```text
join   10 replies after 1,163 ms; quotes waiting at the same time:  1
async  10 replies after   146 ms; quotes waiting at the same time: 10
```

The first line is the draft. The tenth customer waited more than a second, and the courier never saw more than one question at a time. The clerk asked for a price, held the phone until the answer came, and only then opened the next letter. Ten customers, ten phone calls, one after another.

The fix hands the ticket back to the loop and finishes later:

@@ASYNC@@

Let's read it in order. First we ask for the price, which returns at once (1). We keep the future in `inFlight`, the set of requests we've read and not yet answered. Then `whenCompleteAsync` tells the future what to do once the price arrives (2): drop the future from the set and write the reply. `channelRead0` now returns in microseconds. The second line of the demo shows the result: all ten customers answered in 146 ms, with ten prices on the way at once.

The second argument, `ctx.executor()`, is the one tricky part. It picks the thread that runs the **callback**, the piece of code handed over to run later. `ctx.executor()` is the channel's own event loop, so the callback goes into the clerk's in-tray, the queue of small jobs the loop runs between reads. That matters because the handler keeps state: the set of futures in flight. With plain `whenComplete`, the callback would run on whatever thread finished the future, a courier's thread, while the loop adds to the same `HashSet` in `channelRead0`. That's the lost update from Race conditions: why count++ lies, with a set instead of a counter. When every touch of the handler's state happens on the loop, you need no lock: the loop is the lock. `ctx.writeAndFlush` would be safe from any thread. The set is not.

**A handler that waits makes every channel on its loop wait. Hand the future back, and finish on the loop.**

The interface carries the other half of the rule. `quote` must return at once and complete the future later, from any thread. Lesson 2 of this track keeps that promise with `scope.future { }`, which starts a coroutine and returns its ticket at once. A `runBlocking { }` in its place would block the loop exactly like `join()`.

How do we prove the loop is free? Netty: the event loop and the channel pipeline used a lag probe: slip an empty task into the in-tray and time how long it waits. Its lab asserted under 300 ms. That holds on a quiet laptop. On a build machine running eight builds on four cores, a healthy loop can miss 300 ms, and a broken handler can pass when the fake courier answers fast. So this lab's test counts instead of timing. It holds 100 quotes open, checks that the source saw 100 calls, then checks that the loop ran 50 empty tasks. A loop stuck in `join()` shows 1 call, on any machine and at any load. The worked example builds that test step by step.

The loop is free now. It reads as fast as clients send, and some clients send a great deal.""", JOIN=pair(J_JOIN, K_JOIN), ASYNC=pair(J_ASYNC, K_ASYNC))

S3 = fill("""A client may pipeline: send many requests without waiting for a single reply. Say one client sends 20,000 requests and doesn't read its replies for half a second. Two things grow in the server's memory. Each request that waits for its price is a future in the in-flight set. And each reply the client hasn't read yet waits in the channel's outbound buffer, the queue of bytes Netty keeps until the network can take them. Netty in practice: codecs, flow control and leaks pictured it as the out-tray behind each box. `writeAndFlush` never blocks, so the out-tray simply fills. Nothing limits either one.

Netty gives you one control, **auto-read**: whether the loop keeps reading a channel. While it's on, the loop reads the connection whenever bytes arrive. Turn it off, and the clerk stops taking letters from that box. The operating system's buffers for that connection fill up, and TCP makes the client wait before it sends more. It's the packer's slip from the Reactive track, "send me 10 more", carried by the network itself: the server asks for more only when it has room. That's **backpressure**, a slow receiver slowing down a fast sender. Here the post office picture breaks, in our favour: a clerk who stops taking letters leaves a queue at the door, but a server that stops reading leaves the waiting in the network's buffers and the client's own, not in its memory.

The out-tray has two painted marks that say when there's room. They are Netty's water marks, 32 KiB low and 64 KiB high by default. When the bytes waiting pass the high mark, `isWritable()` turns false. When they drain below the low mark, it turns true again. Our policy is one rule, applied after every new request, after every reply, and whenever writability changes:

@@RULE@@

Read it aloud: read this customer only while their replies can leave and fewer than 16 of their questions are waiting. The cap of 16 bounds the futures one connection can hold. The writability check bounds the out-tray.

There's a catch, and the demo shows it. Turning auto-read off stops the next socket read. It doesn't stop the lines the decoder already has. One read can bring 64 KB, a few thousand requests, and `LineBasedFrameDecoder` hands every one of them to the handler before the loop looks at auto-read again. `FlowControlHandler`, placed between the decoders and our handler, closes that gap. While auto-read is off, it keeps the decoded lines in a queue of its own, like opened letters left in a tray on the clerk's desk, and passes them on one at a time as reading resumes.

The demo pipelines 20,000 requests and reads nothing for 500 ms. One run printed:

| Policy | Requests taken while the client read nothing | Peak outbound buffer |
|---|---|---|
| none | 8,835 | 2,084,596 bytes |
| the auto-read rule | 2,993 | 716,915 bytes |
| the rule and `FlowControlHandler` | 1,234 | 67,584 bytes |

The two lower rows took the same number of requests in the Java run and the Kotlin run. The first row moves with the machine's load: how much the server swallows depends on how busy it is, and its queue reached between 1.6 and 2.5 MB in the runs made for this lesson. The last peak is the 64 KiB high water mark (65,536 bytes) plus a few replies. Every client still got all 20,000 replies once it read them. The lab tests the cap directly: 40 pipelined requests against a source that holds every quote must produce exactly 16 calls.

**Writes never block, so your memory does the waiting. Read only while the client keeps up.**

We can take requests and pace them now. What's left is how a connection ends, and there are four ways.""", RULE=pair(J_RULE, K_RULE))

S4 = fill("""A connection ends in one of four ways, and each has its own code path.

The client sends `QUIT`. The server writes `BYE` and closes from the write's future, with `ctx.writeAndFlush("BYE\\n").addListener(ChannelFutureListener.CLOSE)`. A `ChannelFuture` is Netty's ticket for a write, and the listener runs once the bytes have left. Closing right after `flush()` can drop bytes still in the out-tray; Netty in practice lost 57,344 bytes that way.

A line is too long. `LineBasedFrameDecoder` throws `TooLongFrameException`, and Netty passes it to the handler's `exceptionCaught`. The server answers `ERR line too long` and closes the same way. A client that sends 100 bytes where 64 are allowed is broken or hostile, and neither deserves a long conversation.

The client hangs up. `channelInactive` runs on the loop, and the handler cancels every future still in its set, because nobody is left to read those answers. For a plain `CompletableFuture`, `cancel` interrupts nothing, as CompletableFuture: errors, timeouts and fan-out showed: it only marks the ticket as void. It's the guests calling dinner off with nobody passing the news to the kitchen. Lesson 2 of this track turns that cancel into one that reaches all three courier calls.

The server shuts down. Pools in production: names, errors, context, shutdown closed the kitchen in a fixed order, and a server closes the same way:

@@CLOSE@@

First, `stopAccepting()` closes the listening socket, the one that takes new connections, so nobody new walks in while the rest shuts down (1). Then we close every open connection (2). `connections` is a `ChannelGroup`, a set of channels that drops each one when it closes, and the server adds every new channel to it. Closing the group closes each connection on its own loop, every handler sees `channelInactive` and cancels its work, and only then does `shutdownGracefully` stop the loop threads (3).

You may wonder why step 2 is needed at all, since `shutdownGracefully` also closes the channels it still finds. In this track's test runs, that wasn't reliable: in about one run in three, a client still saw its connection open after the loops had stopped. Closing the connections ourselves makes the order plain. Lesson 3 of this track adds one more step between the first two lines: a short grace period in which prices already on their way can still be answered.

Check yourself before the lab: a client has two requests pending when `close()` runs. What does it read from its socket, and what happens to the two futures? (It reads the end of the stream, because its channel was closed. Both futures are cancelled in `channelInactive`.)

The counter is finished, and it still has nothing real to sell: the lab's fake source makes up its prices. Next sitting, the couriers get their phone calls.""", CLOSE=pair(J_CLOSE, K_CLOSE))

ASIDE = {
    "title": "If you write web services, is this loop yours too?",
    "body": "Often, yes. Vert.x, a toolkit built on Netty, runs your handlers on these same event loops, as Vert.x: event loops, verticles and the golden rule showed. Quarkus, a framework for web services built on Vert.x, runs an endpoint that returns a reactive type on them as well. A call such as `.await().indefinitely()` inside such an endpoint is this lesson's `join()`: it stalls every request on that loop, not just its own. Vert.x even notices, with its blocked-thread checker, but only after the loop has been stuck for two seconds."
}

# ---- worked example: the counting test ----
W1J = """final class FakeSource implements QuoteSource {
    private final List<CompletableFuture<Quote>> pending = new ArrayList<>();   // guarded by this
    private int calls;

    @Override
    public synchronized CompletableFuture<Quote> quote(String destination) {
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
    override fun quote(destination: String): CompletableFuture<Quote> {
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
    CompletableFuture<Quote> quote = source.quote(r.destination());
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
    val quote = source.quote(r.destination)
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
    CompletableFuture<Quote> quote = source.quote(r.destination());   // returns at once
    inFlight.add(quote);
    updateReading(ctx);
    quote.whenCompleteAsync((q, e) -> {                               // runs on this channel's loop
        inFlight.remove(quote);
        if (ctx.channel().isActive()) ctx.writeAndFlush(e == null ? ok(r.id(), q) : error(r.id(), e));
        updateReading(ctx);
    }, ctx.executor());
}

// the rule: read only while writable and under the cap
// setAutoRead(ctx.channel().isWritable() && inFlight.size() < MAX_IN_FLIGHT)"""
DRILL_K = """override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
    val r = QuoteProtocol.parse(line)
    val quote = source.quote(r.destination)                           // returns at once
    inFlight += quote
    updateReading(ctx)
    quote.whenCompleteAsync({ q, e ->                                 // runs on this channel's loop
        inFlight -= quote
        if (ctx.channel().isActive) ctx.writeAndFlush(if (e == null) ok(r.id, q) else error(r.id, e))
        updateReading(ctx)
    }, ctx.executor())
}

// the rule: read only while writable and under the cap
// isAutoRead = ctx.channel().isWritable && inFlight.size < MAX_IN_FLIGHT"""

CLOSING = """We started at the post office counter, with a customer asking for a price to Lisbon and a clerk who must never make the phone call. Now the counter hands each question back as a ticket and finishes it on its own loop. It stops reading a customer who stops listening, and it closes in order.

Now look in your own code for `join()`, `get()`, `block()` or `runBlocking` inside a callback that runs on an event loop. Each one is the clerk on the phone.

Next, we'll make the phone calls with Kotlin coroutines. How do we ask three couriers together, keep the answers that arrive in time, and stop the calls when the customer walks away?"""

L = {
 "id": "cap2-01",
 "title": "A Netty server that never blocks its loop",
 "minutes": 40,
 "goal": "By the end you can build the shell of a non-blocking quote service on Netty 4.2 (a line protocol with request ids and a length limit, a handler that never waits on its event loop, reading that pauses when a client stops reading, and a clean close) and prove that the loop stays free with a test that counts instead of timing.",
 "opening": OPENING,
 "warmup": {
  "q": "Our server has one event loop. Its handler calls `source.quote(destination).join()`, and each price takes the courier 100 ms. Ten customers send one request each at the same moment. When does the last one get its reply?",
  "options": [
   "After about 100 ms: the ten prices are fetched at the same time",
   "After about 1 second: the loop waits for each price in turn",
   "After about 200 ms: Netty starts a second loop when the first one is busy",
   "Never: Netty throws when a handler calls `join()`"
  ],
  "answer": 1,
  "why": "The loop is one thread, and `join()` holds it for the whole 100 ms. It reads the next request only after the current price is back, so the ten prices come one after another: about 1,000 ms (1,163 ms in one run of this lesson's demo). Netty never adds loops on its own, and it doesn't notice blocking. Handing the future back lets all ten wait at once, and the same demo then answers everyone in about 100 to 150 ms."
 },
 "sections": [
  {
   "h": "The service we'll build, and the one rule it never breaks",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One event loop carries every request through the pipeline. The handler asks the source for a future and gets the callback back on the same loop, and auto-read decides when it takes the next line."},
   "try": {
    "title": "Feed the pipeline by hand",
    "minutes": 4,
    "steps": [
     "Open `ProtocolDemo.java` (or `ProtocolDemo.kt`). It pushes bytes into a line pipeline with `EmbeddedChannel`, Netty's channel for tests, which has no socket at all. Then it completes the two prices by hand, Dublin first.",
     "Predict what comes out after each of the five steps, and whether the channel is still open at the end.",
     "Run it. Then run it again with `-Pargs=6`, a 6-byte line limit. Predict first: `7 LISBON` is 8 bytes."
    ],
    "code": demo("ProtocolDemo"),
    "expect": "Half a line produces nothing. The second write completes both requests, but nothing comes out until a price arrives. Dublin answers first, so `8 OK DUBLIN 9.80 fjord` leaves before `7 OK LISBON 12.42 northline`: the ids are what let a client match them. The 100-byte line gets `ERR line too long`, and the channel closes. With a 6-byte limit, the second write already fails: `7 LISBON` is too long, the channel closes, and the later steps find nothing to do."
   },
   "refs": [
    {"title": "LineBasedFrameDecoder source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/codec-base/src/main/java/io/netty/handler/codec/LineBasedFrameDecoder.java", "kind": "docs"}
   ]
  },
  {
   "h": "Hand the future back instead of waiting on the loop",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "Ten customers, one loop, two handlers",
    "minutes": 4,
    "steps": [
     "Open `BlockedLoopDemo.java` (or the Kotlin twin). One event loop serves ten clients, and the courier answers each price after 100 ms.",
     "Predict the time until all ten replies, and the most prices waiting at the same time, for `join` and for `async`.",
     "Run it. Then change the group to `new MultiThreadIoEventLoopGroup(2, ...)`, two loops, and predict the `join` numbers again."
    ],
    "code": demo("BlockedLoopDemo"),
    "expect": "`join`: a little over 1,000 ms (1,163 ms in one run here) and 1 price at a time, because the loop waits for each price before it reads the next request. `async`: about 100 to 150 ms and 10 at once. With two loops, the ten connections are split five and five, so `join` takes about 500 ms with 2 prices at a time. More clerks divide the damage; they don't remove it."
   },
   "refs": [
    {"title": "CompletableFuture (Java SE 25 API): whenCompleteAsync", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html", "kind": "docs"}
   ]
  },
  {
   "h": "Auto-read: the one tap that stops a client who won't listen",
   "body": S3,
   "try": {
    "title": "Pipeline 20,000 requests at a server, and read nothing",
    "minutes": 5,
    "steps": [
     "Open `BackpressureDemo.java` (or the Kotlin twin). It runs the same server three times: no policy, the auto-read rule, and the rule plus `FlowControlHandler`.",
     "Run it and compare the three lines.",
     "Change `MAX_IN_FLIGHT` to 1. Predict the third line: does the peak change much, and do all 20,000 replies still arrive?"
    ],
    "code": demo("BackpressureDemo"),
    "expect": "No policy: the server swallows thousands of requests (8,835 in one run here; the number changes from run to run) and queues 1.6 to 2.5 MB of replies. The rule alone: about 3,000 requests and about 700 KB, because one read brought thousands of lines and the decoder delivered them all. With `FlowControlHandler`: about 1,200 requests and about 67,600 bytes, just above the 64 KiB high water mark. With a cap of 1, the peak stays near the high water mark (writability is what stops it), and every reply still arrives, more slowly, one request at a time."
   },
   "refs": [
    {"title": "FlowControlHandler source and Javadoc, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/handler/src/main/java/io/netty/handler/flow/FlowControlHandler.java", "kind": "docs"}
   ]
  },
  {
   "h": "Closing on purpose: four ways a connection ends",
   "body": S4,
   "refs": [
    {"title": "WriteBufferWaterMark source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/WriteBufferWaterMark.java", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The non-blocking handler in Java and Kotlin",
  "java": {"title": "QuoteHandler.java (core)", "src": COMPARE_J},
  "kotlin": {"title": "QuoteHandler.kt (core)", "src": COMPARE_K},
  "note": "Both versions are the same handler at runtime. Netty sees a `SimpleChannelInboundHandler<String>`, and the Kotlin lambda becomes a `BiConsumer` through SAM conversion, Kotlin's way of passing a lambda where Java expects a one-method interface. One Kotlin detail needs care. `whenCompleteAsync` comes from Java, so `q` and `e` arrive as platform types, whose nullness Kotlin doesn't know, and Kotlin won't stop you calling `q.price` when the future failed and `q` is null. Declare them `Quote?` and `Throwable?`, and the compiler makes you check. Kotlin also tempts you with one thing Java doesn't have: `runBlocking { }` around a suspend call inside `channelRead0`. It blocks the loop exactly like `join()`. Lesson 2 of this track shows the bridge that doesn't: `scope.future { }`, which returns at once."
 },
 "worked": {
  "title": "Write the test that proves the loop is free, by counting",
  "steps": [
   {"say": "Decide what to count. Hold every price open, so a blocked loop stays blocked for the whole test, and count something the loop can do only while it is free: calls that reach the source. The fake keeps each future until the test releases it.",
    "code": W1J, "lang": "java", "alt_code": W1K, "alt_lang": "kotlin"},
   {"say": "Add a probe: hand the loop empty tasks and count how many ran. The 5-second wait only bounds how long a failure takes to report. The assertion is on the count, so a slow machine can't fail a healthy loop.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Spread 100 requests over 10 connections. One connection may hold only 16 requests (section 3), so 100 on one connection would test the cap instead of the loop. Assert both counts, then release the prices and check that every id came back on the right connection.",
    "code": W3J, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"},
   {"say": "Release the prices in `finally`. A broken handler is stuck in `join()`; completing its future wakes the loop, so the server can close and the next test starts clean. Self-check: against the first-draft handler, which assertion fails, and with what number? (The first one: `expected: 100 but was: 1`. The loop took one request and has been waiting in `join()` ever since.)",
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
   "Run the tests. All eight fail. Read `QuoteProtocol.java` (the shape of every line) and `QuoteSource.java` (the contract: return at once). The tests' fake source is in `src/test/.../l01/FakeSource.java`.",
   "Write `QuotePipeline.handlers`: the five handlers, in the order its Javadoc lists. The framing and `QUIT` tests should pass now.",
   "Fix point 1 in `QuoteHandler`: add a `Set<CompletableFuture<Quote>> inFlight` field, keep each future in it, and write the reply in `whenCompleteAsync(..., ctx.executor())`. Skip the write if the channel is no longer active.",
   "Add `updateReading` (point 2), and call it after adding a future, after each reply, and in `channelWritabilityChanged`.",
   "Cancel the futures in flight in `channelInactive` (point 3), and answer a line that is too long in `exceptionCaught` (point 4).",
   "Write `QuoteServer.close()` in the order its Javadoc gives. Run the tests until all eight pass, then run them twice more."
  ],
  "hints": [
   "If the 100-pending test says `expected: 100 but was: 1`, the loop is still inside `join()` somewhere in `channelRead0`.",
   "If the `MAX_IN_FLIGHT` test sees more than 16 calls, check that `FlowControlHandler` sits between the decoders and `QuoteHandler`, and that you call `updateReading` right after adding the future.",
   "`whenCompleteAsync` runs the callback as a task on the loop. In the `EmbeddedChannel` tests, the replies appear after `runPendingTasks()`, which the tests call for you.",
   "`exceptionCaught` receives the `TooLongFrameException` itself. `QUIT` shows how to close after a write: `ctx.writeAndFlush(...).addListener(ChannelFutureListener.CLOSE)`."
  ],
  "done_when": "All eight tests in `QuoteServerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the non-blocking reply from memory",
  "minutes": 4,
  "prompt": "Close the lab. In a `SimpleChannelInboundHandler<String>` with a `QuoteSource source` and a `Set` called `inFlight`, write `channelRead0` so that it asks for the price, keeps the future while it is pending, and writes the reply on the channel's own event loop. Then write the auto-read rule as one line. Which argument decides the thread that runs your callback?",
  "answer": {"lang": "java", "src": DRILL_J, "alt": {"lang": "kotlin", "src": DRILL_K}}
 },
 "recap": [
  "The program is a quote service: `7 LISBON` gets back `7 OK LISBON 12.42 northline`, the cheapest courier's price, with the same id. This sitting built its Netty shell: a line protocol, a 64-byte line limit, and a `QuoteSource` that returns a future.",
  "The event loop never waits. `join()`, `get()` or `runBlocking` in a handler stalls every channel on that loop. Hand the future back and finish in `whenCompleteAsync(..., ctx.executor())`, which keeps the handler's state on one thread.",
  "Prove it by counting: hold prices open, then count calls and probe tasks. A blocked loop shows 1 call whatever the machine's speed, while a time limit can fail a healthy loop on a busy machine.",
  "Auto-read is the only tap: read while the channel is writable and fewer than 16 requests wait. `FlowControlHandler` holds lines already decoded, which took the demo's peak from about 700 KB down to 67,584 bytes.",
  "Close on purpose: `BYE` and errors close from the write's future, a hang-up cancels the futures in flight, and the server stops accepting, closes its connections, and only then stops its loops.",
  "Where today's shell stops: its source is a stand-in, and cancelling a plain `CompletableFuture` stops none of the work behind it. Lesson 2 fixes both."
 ],
 "closing": CLOSING,
 "quiz": [
  {
   "q": "The server runs 8 event loops with 800 connections, and the first-draft handler calls `source.quote(d).join()`. One courier stalls for 2 seconds on a single request. Who waits?",
   "options": [
    "Only the client whose price stalled",
    "All 800 clients: Netty runs one handler at a time for the whole server",
    "About 100 clients: every connection registered on the same loop as that request",
    "Nobody: `join()` parks the loop thread and Netty moves its channels to another loop"
   ],
   "answer": 2,
   "why": "Netty spreads channels over the 8 loops in turn, and each stays where it was registered: about 100 per loop. The loop running `join()` can't read, decode or write for any of its channels for 2 seconds, while the other 7 loops carry on. Netty never moves a channel to another loop.",
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
   "why": "`writeAndFlush` never blocks. The kernel's buffers are small and fill first; after that, Netty keeps the bytes in the channel's outbound buffer, in your own memory. In one run of this lesson's demo, that reached 2,084,596 bytes. Only reading less from that client stops it growing.",
   "from": "io-04"
  },
  {
   "q": "`QuoteHandler` finishes each price with `whenCompleteAsync(callback, ctx.executor())`. What goes wrong with plain `whenComplete(callback)`?",
   "options": [
    "The callback runs on the thread that completed the future, so it races the event loop on the in-flight `HashSet`",
    "`writeAndFlush` throws, because it may only be called on the event loop",
    "Nothing: the two behave the same",
    "The callback never runs, because the loop doesn't know about it"
   ],
   "answer": 0,
   "why": "`whenComplete` runs the callback on whichever thread completes the future, here a courier's thread, while the loop adds to the same set in `channelRead0`. That's a read-modify-write race on a plain `HashSet`. `writeAndFlush` itself is safe from any thread, which is why the bug is easy to miss."
  },
  {
   "q": "In Reactive Streams, a subscriber paces the publisher with `request(n)`, the packer's slip. What plays that part between this server and one client?",
   "options": [
    "The 64-byte line limit",
    "Auto-read, switched on only while the channel is writable and fewer than 16 requests wait",
    "TCP's receive window on its own, with no code in the server",
    "The 64 KiB high water mark on its own"
   ],
   "answer": 1,
   "why": "Auto-read is the server's demand signal: it reads more only when it has room, and TCP carries the pause back to the client. TCP alone does nothing while the server keeps reading, because the bytes just move from the kernel into the server's memory. The water mark only reports a full out-tray; your handler has to act on it.",
   "from": "rx-01"
  },
  {
   "q": "When a client hangs up, `channelInactive` calls `cancel(true)` on a pending future from a source that runs blocking calls with `supplyAsync` on a thread pool. What happens to the courier call?",
   "options": [
    "It is interrupted and stops at once",
    "The pool thread is stopped",
    "It runs to the end, and its result is dropped: `cancel` only completes the future",
    "The cancel fails, because the work has already started"
   ],
   "answer": 2,
   "why": "`CompletableFuture.cancel` completes the future with a `CancellationException` and doesn't interrupt the thread doing the work, whatever you pass. The call finishes, and its result goes nowhere. To stop the work itself, the source has to react to the cancel, which is what lesson 2's coroutines do.",
   "from": "exec-07"
  }
 ],
 "flashcards": [
  {"front": "What does `join()` in a Netty handler cost?", "back": "Every channel on that event loop waits until the future completes, not just the one that asked."},
  {"front": "Why finish with `whenCompleteAsync(callback, ctx.executor())`?", "back": "The callback runs on the channel's own event loop, so the handler's state is only ever touched by one thread."},
  {"front": "When should the quote server read a connection?", "back": "Only while the channel is writable and fewer than `MAX_IN_FLIGHT` (16) of its requests are waiting for a price."},
  {"front": "What does `FlowControlHandler` add when auto-read is off?", "back": "It holds messages the decoder already produced and releases them as reading resumes. Auto-read alone only stops the next socket read."},
  {"front": "Why count instead of time in a test that proves the loop is free?", "back": "A healthy loop can miss a time limit on a busy machine. A blocked loop's counts (1 call, 0 probe tasks) don't depend on speed."},
  {"front": "Why does the quote protocol carry a request id?", "back": "A reply leaves when its price arrives, so replies can overtake each other. The client matches them by id."},
  {"front": "In what order does the server shut down?", "back": "Stop accepting, close every open connection (a `ChannelGroup`; handlers cancel their work in flight), then `shutdownGracefully` to stop the loop threads."}
 ],
 "terms": [
  {"term": "Quote service", "plain": "A program that gives a price for a job before anyone books it; here, the price of sending a parcel."},
  {"term": "Event loop", "plain": "One thread that reads, decodes and writes for every channel registered with it, plus a queue of tasks."},
  {"term": "Pipelining", "plain": "A client sends many requests without waiting for the replies."},
  {"term": "In-flight request", "plain": "A request the server has read but not yet answered."},
  {"term": "Auto-read", "plain": "Whether the loop keeps reading a channel's socket. Off means the kernel's buffers fill and TCP makes the client wait."},
  {"term": "FlowControlHandler", "plain": "A Netty handler that holds already-decoded messages while auto-read is off."},
  {"term": "Request id", "plain": "A number the client puts on a request and the server repeats on the reply, so replies can arrive in any order."},
  {"term": "Probe task", "plain": "An empty task handed to an event loop to check that it still runs work."}
 ],
 "explain_back": {
  "prompt": "A colleague reviews your handler: \"Why all this ceremony? The couriers answer in 5 ms, so `join()` is fine, and Netty buffers writes for us anyway.\" Explain what `join()` costs on an event loop, why the callback runs on `ctx.executor()`, and why the server needs the auto-read rule.",
  "answer": "An event loop is one thread that serves every channel registered with it, so `join()` doesn't cost 5 ms for one client: it costs 5 ms for every client on that loop, on every request. Under load, that is a queue that never drains, and when a courier stalls for two seconds, every connection on the loop freezes for two seconds. Handing the future back lets the loop keep reading and writing while any number of prices are on their way. The callback runs on `ctx.executor()` so that the handler's state, the set of futures in flight, is only touched by the loop thread; with plain `whenComplete`, a courier's thread would race the loop on that set. Netty does buffer writes, but without limit: a client that pipelines and doesn't read makes the outbound buffer and the set of pending futures grow in our memory. Auto-read is the one control we have, so we read only while the channel is writable and fewer than 16 requests wait, with `FlowControlHandler` holding lines the decoder already produced. In the demo, that kept the peak at about 67 KB instead of about 2 MB."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three things a production shell adds to this one.\n\nAn idle timeout. A client that connects and never sends a line holds a channel forever. `IdleStateHandler` fires an `IdleStateEvent` through `userEventTriggered` after a connection has been quiet for the time you set; close the channel there.\n\nTLS, the encryption behind `https`. An `SslHandler` goes first in the pipeline, before the frame decoder, and nothing after it changes. That is the payoff of keeping every concern in its own handler.\n\nLoop metrics. Every loop of a `MultiThreadIoEventLoopGroup` is a `SingleThreadEventExecutor`, and `pendingTasks()` is the length of its task queue, the clerk's in-tray. In this server, every reply is a task, so a queue that keeps growing is a loop that can't keep up. Report it for each loop.\n\nTwo limits of this lesson's design are worth knowing. The cap of 16 protects the server from one greedy client and does nothing against ten thousand polite ones: lesson 3 of this track adds a limit for the whole service that turns work away with a clear error. And `whenCompleteAsync` costs a hand-off per reply, even when the price is already there. That is cheap next to a trip across the network, and it buys a handler whose state needs no lock.\n\nFinally, the counting probe has a stronger cousin for tests: BlockHound, a separate Java agent library, throws as soon as code on a Netty event-loop thread calls a known blocking method such as `CompletableFuture.join` or `Thread.sleep`. Netty ships the integration for it (`Hidden$NettyBlockHoundIntegration` in `netty-common`)."
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
