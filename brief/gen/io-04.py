import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l04"
K = "kotlin/workbench/nio/l04"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 680 262" role="img" aria-label="One frame on the wire: a 4-byte length of 7, a type byte, and the body auth-1. '
    'LengthFieldBasedFrameDecoder with arguments 1024, 0, 4, 0, 4 strips the length and passes on the type and body, '
    'which the payment decoder turns into a message">'
    '<text class="t-s t-m" x="20" y="24">on the wire</text>'
    '<rect class="box-b" x="20" y="34" width="210" height="40" rx="8"/>'
    '<text class="t t-code" x="125" y="59" text-anchor="middle">00 00 00 07</text>'
    '<rect class="box-a" x="240" y="34" width="60" height="40" rx="8"/>'
    '<text class="t t-code" x="270" y="59" text-anchor="middle">01</text>'
    '<rect class="box-ok" x="310" y="34" width="250" height="40" rx="8"/>'
    '<text class="t t-code" x="435" y="59" text-anchor="middle">61 75 74 68 2d 31</text>'
    '<text class="t-s t-b" x="125" y="94" text-anchor="middle">length: int32 = 7</text>'
    '<text class="t-s t-a" x="270" y="94" text-anchor="middle">type</text>'
    '<text class="t-s t-ok" x="435" y="94" text-anchor="middle">body: "auth-1" in UTF-8</text>'
    '<text class="t-s t-m" x="125" y="112" text-anchor="middle">offset 0, 4 bytes long</text>'
    '<text class="t-s t-m" x="352" y="112" text-anchor="middle">7 = 1 + 6: the length counts what follows it</text>'
    '<line class="ln-a" x1="620" y1="124" x2="620" y2="174" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="435" y="146" text-anchor="middle">LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)</text>'
    '<text class="t-s t-bad" x="125" y="146" text-anchor="middle">strip 4: the length is gone</text>'
    '<text class="t-s t-m" x="20" y="170">frame passed on</text>'
    '<rect class="box-a" x="240" y="180" width="60" height="40" rx="8"/>'
    '<text class="t t-code" x="270" y="205" text-anchor="middle">01</text>'
    '<rect class="box-ok" x="310" y="180" width="250" height="40" rx="8"/>'
    '<text class="t t-code" x="435" y="205" text-anchor="middle">61 75 74 68 2d 31</text>'
    '<text class="t-s" x="400" y="246" text-anchor="middle">PaymentFrameDecoder makes it PaymentMessage(1, &quot;auth-1&quot;)</text>'
    '</svg>'
)

L = {
 "id": "io-04",
 "title": "Netty in practice: codecs, flow control and leaks",
 "minutes": 38,
 "goal": "By the end you can frame and decode a binary protocol with Netty codecs, say who must release each ByteBuf and catch a leak with PARANOID detection in a test, and stop a slow peer from filling your memory with writability and auto-read.",
 "warmup": {
  "q": "A Netty echo handler calls `ctx.write(msg)` for every message, and the client reads ten times slower than it sends. What happens to the bytes the server can't send yet?",
  "options": [
   "`ctx.write` blocks until the client catches up",
   "Netty drops them and logs a warning",
   "They queue in the channel's outbound buffer in your process, which keeps growing unless your code reacts",
   "The kernel stores them all in the socket's send buffer"
  ],
  "answer": 2,
  "why": "`write` never blocks the event loop. Netty queues the message in the channel's outbound buffer and writes it when the socket has room. The kernel's send buffer is small and fills first, so the rest piles up in your heap or direct memory. In this lesson's demo the queue peaked at 1.3 to 1.9 MB for 8 MiB of echo, and a test run of the same code saw the whole 16 MB payload waiting."
 },
 "sections": [
  {
   "h": "Frame first, then decode",
   "body": """TCP delivers a stream of bytes, not messages (lesson 2). So the first job of any protocol pipeline is framing: finding where one message ends and the next begins. The payment link in this lesson's lab uses the most common framing for binary protocols, a length prefix:

```text
[ length: int32 ][ type: int8 ][ body: UTF-8 bytes ]      length = 1 + body bytes
```

Here is a frame decoder written by hand. Netty's `ByteToMessageDecoder` is a handler that keeps every byte that has arrived so far in one buffer (Netty calls it the cumulation) and calls your `decode` each time more bytes arrive. Your job is to take out whole frames and leave the rest for later:

```java
class HandMadeFrameDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
        if (in.readableBytes() < 4) return;              // 1. not even the length yet
        int length = in.getInt(in.readerIndex());        // 2. peek, don't consume
        if (length > 1020) throw new TooLongFrameException("frame too long: " + length);
        if (in.readableBytes() < 4 + length) return;     // 3. body incomplete: wait for more
        in.skipBytes(4);
        out.add(in.readRetainedSlice(length));           // 4. one whole frame, no copy
    }
}
```

```kotlin
class HandMadeFrameDecoder : ByteToMessageDecoder() {
    override fun decode(ctx: ChannelHandlerContext, input: ByteBuf, out: MutableList<Any>) {
        if (input.readableBytes() < 4) return            // 1. not even the length yet
        val length = input.getInt(input.readerIndex())   // 2. peek, don't consume
        if (length > 1020) throw TooLongFrameException("frame too long: $length")
        if (input.readableBytes() < 4 + length) return   // 3. body incomplete: wait for more
        input.skipBytes(4)
        out += input.readRetainedSlice(length)           // 4. one whole frame, no copy
    }
}
```

Each line follows a rule from the `ByteToMessageDecoder` Javadoc. Return without moving the reader index when a frame is incomplete. Use `getInt(in.readerIndex())`, not `getInt(0)`, because the cumulation can still hold consumed bytes in front of the reader index. Hand the frame on as a slice, a view of the same memory, because `readBytes(n)` allocates a new buffer that someone must release. And never mark a `ByteToMessageDecoder` `@Sharable`: it keeps per-channel state.

You don't have to write it. `new LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)` does the same job: frames of at most 1024 bytes, a length field at offset 0 that is 4 bytes long, no adjustment (the length counts only what follows it), and strip 4 bytes before passing the frame on. The figure shows each number on the wire. The next decoder sees exactly `[type][body]` and turns it into a `PaymentMessage`. On the way out, a `MessageToByteEncoder<PaymentMessage>` writes the three fields back.

The maximum is a security setting. A client that sends a length of two billion would make a decoder without one buffer two gigabytes while it waits. With it, the demo's hostile frame fails at once with `Adjusted frame length exceeds 1024: 5004 - discarded` (5,000 plus the 4-byte length field).""",
   "figure": {"svg": FIG, "caption": "The four numbers after 1024 say where the length is, how long it is, how to adjust it, and how many bytes to strip before the next decoder."},
   "try": {
    "title": "Feed a codec in awkward pieces",
    "minutes": 4,
    "steps": [
     "Open `CodecDemo.java` (or `CodecDemo.kt`). It encodes two frames, 11 and 14 bytes long, and feeds them to a server pipeline cut at bytes 3, 9 and 14.",
     "Predict which of the four slices produce a reply, and which reply.",
     "Run it. Then change the cut at 9 to 11 and predict again."
    ],
    "code": {"lang": "java", "title": "CodecDemo.java", "src": read(f"{lab}/demo/{P}/CodecDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.CodecDemo",
             "file": f"{lab}/demo/{P}/CodecDemo.java",
             "alt": {"lang": "kotlin", "title": "CodecDemo.kt", "src": read(f"{lab}/demo/{K}/CodecDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.CodecDemoKt",
                     "file": f"{lab}/demo/{K}/CodecDemo.kt"}},
    "expect": "Slices [0,3) and [3,9) produce nothing: half a length field, then an incomplete body. Slice [9,14) completes frame 1 (11 bytes) and starts frame 2, so `type=2 AUTH-1` comes out. Slice [14,25) completes frame 2: `type=8 CAPTURE-1`. With the cut at 11 instead, slice [3,11) completes frame 1 exactly, and [11,14) produces nothing. The decoder waits for whole frames, wherever the cuts fall."
   }
  },
  {
   "h": "A ByteBuf has two indexes and a reference count",
   "body": """Netty's `ByteBuf` fixes the two things that made `ByteBuffer` painful in lesson 2. It has separate `readerIndex` and `writerIndex`, so there is no read mode, no write mode and no `flip()`. And it is reference-counted, so Netty can pool its memory.

Pooling is the reason for the counting. Netty allocates direct memory, outside the Java heap, because the kernel can read it without a copy. Direct memory is costly to allocate, so Netty's allocator carves buffers out of big chunks and takes them back for reuse. The garbage collector can't do that hand-back: it frees an object at some unknown later time, when heap pressure says so, while a busy server needs the memory back the moment a message is done. So every `ByteBuf` carries a count. It starts at 1, `retain()` adds one, `release()` subtracts one, and at 0 the memory goes back to the pool. Touch the buffer after that and Netty throws:

```text
buffer(16): AdaptiveByteBuf direct=true readerIndex=0 writerIndex=0 refCnt=1
after writeInt+writeLong: writerIndex=12 readableBytes=12
after readInt: readerIndex=4 readableBytes=8 (no flip)
retain(): refCnt=2
release() -> false, refCnt=1
release() -> true, refCnt=0 (memory goes back to the allocator)
readLong() after release -> IllegalReferenceCountException: refCnt: 0
```

`AdaptiveByteBuf` comes from the adaptive allocator, the default since Netty 4.2.

Who calls `release()`? Netty's wiki answers in one sentence: the party that accesses a reference-counted object last is responsible for destroying it. In a pipeline that works out as follows.

- A handler that passes a message on with `ctx.fireChannelRead(msg)` hands over ownership and must not release it.
- A handler that consumes a message and doesn't pass it on must release it. `SimpleChannelInboundHandler` does that for you after `channelRead0` returns.
- A message you `write` belongs to Netty, which releases it once it is on the wire.
- A decoder that turns a buffer into something else releases the input. `ByteToMessageDecoder` and `MessageToMessageDecoder` do it for you.

Get it wrong one way and you release twice: `IllegalReferenceCountException`, loud and immediate. Get it wrong the other way and you leak pooled memory that never comes back, quietly, until the service runs out of direct memory.""",
   "try": {
    "title": "Predict the count",
    "minutes": 3,
    "steps": [
     "Open `RefCountDemo.java` (or `RefCountDemo.kt`). Cover the output above and predict `refCnt` after each line, and what `release()` returns each time.",
     "Run it. Then look at the composite part: `addComponents(true, header, body)` joins two buffers. Predict what `body.refCnt()` is after `frame.release()`."
    ],
    "code": {"lang": "java", "title": "RefCountDemo.java", "src": read(f"{lab}/demo/{P}/RefCountDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.RefCountDemo",
             "file": f"{lab}/demo/{P}/RefCountDemo.java",
             "alt": {"lang": "kotlin", "title": "RefCountDemo.kt", "src": read(f"{lab}/demo/{K}/RefCountDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.RefCountDemoKt",
                     "file": f"{lab}/demo/{K}/RefCountDemo.kt"}},
    "expect": "`release()` returns `false` while the count stays above 0 and `true` when it reaches 0. Reading after that throws `IllegalReferenceCountException: refCnt: 0`. The composite prints `HDR:Payload`: it shares memory with `body`, so the change made through `body` shows up without a copy. `addComponents(true, ...)` transferred ownership, so releasing the composite released both parts: `header.refCnt=0 body.refCnt=0`."
   }
  },
  {
   "h": "PARANOID leak detection catches leaks in tests",
   "body": """A leaked `ByteBuf` doesn't throw. Netty finds leaks after the fact with `ResourceLeakDetector`. It attaches a weak reference to each buffer it tracks, and when the garbage collector collects a tracked buffer whose count never reached 0, the detector logs a report. Tracking costs time, so by default (the `SIMPLE` level) Netty tracks about 1 buffer in 128. `ADVANCED` samples the same way but also records where the buffer was touched. `PARANOID` tracks every buffer with full records, and the Netty wiki recommends it for tests. Turn it on with `-Dio.netty.leakDetection.level=paranoid`, or in a test with `ResourceLeakDetector.setLevel(Level.PARANOID)`.

This is the start of the report from this section's demo, where a handler drops ten buffers without releasing them:

```text
[main] ERROR io.netty.util.ResourceLeakDetector - LEAK: ByteBuf.release() was not called before it's garbage-collected. See https://netty.io/wiki/reference-counted-objects.html for more information.
Recent access records:
#1:
	Hint: 'LeakDemo$1#0' will handle the message from this point.
	...
Created at:
	io.netty.buffer.AdaptiveByteBufAllocator.newDirectBuffer(AdaptiveByteBufAllocator.java:67)
	...
10 buffers leaked; the listener saw 1 report(s): [ByteBuf]
```

Read it from the bottom. `Created at` is where the buffer was allocated, and the access records show who touched it last: the hint names the handler that received it and never let go. Ten buffers leaked, yet there is one report, because the detector reports each distinct access path once.

To fail a build on a leak you need two more pieces. `ByteBufUtil.setLeakListener(...)` gives you a callback per report, so a test can collect them. And detection needs a garbage collection followed by another allocation, because the detector checks its queue of collected buffers when it tracks the next one. The lab's last test does exactly that:

```java
for (int i = 0; i < 40 && leaks.isEmpty(); i++) {
    System.gc();                                    // collect the leaked ByteBuf objects
    Thread.sleep(20);
    ByteBufAllocator.DEFAULT.buffer(8).release();   // the next allocation reports them
}
assertThat(leaks).isEmpty();
```

```kotlin
var i = 0
while (i++ < 40 && leaks.isEmpty()) {
    System.gc()                                     // collect the leaked ByteBuf objects
    Thread.sleep(20)
    ByteBufAllocator.DEFAULT.buffer(8).release()    // the next allocation reports them
}
assertThat(leaks).isEmpty()
```

GC timing makes this check probabilistic, so pair it with a deterministic one: keep a reference to the buffer you pushed in, and assert `refCnt() == 0` after the pipeline ran. The lab does both.""",
   "try": {
    "title": "Make a leak, then fix it",
    "minutes": 4,
    "steps": [
     "Run `LeakDemo` (or `LeakDemoKt`). Predict first: ten leaked buffers, how many reports?",
     "Find the `Hint:` line in the report and match it to the handler in the code.",
     "Fix the handler by adding `ReferenceCountUtil.release(msg);` to `channelRead`, and run it again."
    ],
    "code": {"lang": "java", "title": "LeakDemo.java", "src": read(f"{lab}/demo/{P}/LeakDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.LeakDemo",
             "file": f"{lab}/demo/{P}/LeakDemo.java",
             "alt": {"lang": "kotlin", "title": "LeakDemo.kt", "src": read(f"{lab}/demo/{K}/LeakDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.LeakDemoKt",
                     "file": f"{lab}/demo/{K}/LeakDemo.kt"}},
    "expect": "One `LEAK:` report and `the listener saw 1 report(s): [ByteBuf]`. The hint names the anonymous handler (`LeakDemo$1#0`, or `LeakDemoKt$main$ch$1#0` in Kotlin) as the last owner, and `Created at` points to the `buffer(32)` line. After the fix there is no `LEAK:` line and the listener sees 0 reports."
   },
   "refs": [
    {"title": "Reference counted objects (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Reference-counted-objects.md", "kind": "read"}
   ]
  },
  {
   "h": "Flow control: stop reading when you can't write",
   "body": """`ctx.write(msg)` never blocks, and a slow client never makes it fail. Netty puts the message in the channel's outbound buffer, a queue in your own process's memory, and moves it to the socket when the kernel's send buffer has room. That is handy, and it is also how a Netty service runs out of memory: if the peer reads more slowly than you write, the queue grows without limit.

Netty tells you when the queue gets long. Each channel has two water marks, 32 KiB low and 64 KiB high by default (`WriteBufferWaterMark`). When the bytes waiting in the outbound buffer pass the high mark, `channel.isWritable()` turns false and Netty fires `channelWritabilityChanged`. When they drain below the low mark, `isWritable()` turns true and the event fires again. Two marks instead of one stop it from flipping on every write.

Netty doesn't stop your writes when `isWritable()` is false. You have to act. For an echo server or a proxy, the action is lesson 2's: stop reading from whoever produces the data. `setAutoRead(false)` tells the event loop to stop reading that channel, which for the NIO transport means taking `OP_READ` out of its interest set:

```java
@Override
public void channelReadComplete(ChannelHandlerContext ctx) {
    ctx.flush();
    if (!ctx.channel().isWritable()) ctx.channel().config().setAutoRead(false);   // stop reading
}

@Override
public void channelWritabilityChanged(ChannelHandlerContext ctx) {
    if (ctx.channel().isWritable()) ctx.channel().config().setAutoRead(true);      // drained: read again
    ctx.fireChannelWritabilityChanged();
}
```

```kotlin
override fun channelReadComplete(ctx: ChannelHandlerContext) {
    ctx.flush()
    if (!ctx.channel().isWritable) ctx.channel().config().isAutoRead = false      // stop reading
}

override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
    if (ctx.channel().isWritable) ctx.channel().config().isAutoRead = true         // drained: read again
    ctx.fireChannelWritabilityChanged()
}
```

This section's demo echoes 8 MiB to a client that writes fast and reads slowly. Without those two methods, the outbound buffer peaked at 1,905,344 bytes in one run and 1,332,000 in another, and a test run of the same code for this track saw 16,202,075: the whole payload. With them, the peak was about 129,000 bytes every time. In a proxy you wire it across two channels: the backend's writability switches the frontend's auto-read.

Two more traps showed up while measuring this. Calling `close()` right after the last `flush()` lost 57,344 bytes that were still in the outbound buffer. Close from the write's future instead: `ctx.writeAndFlush(last).addListener(ChannelFutureListener.CLOSE)`. And `channelWritabilityChanged` can fire inside your own `flush()` call, so a handler that writes from that event must cope with being called while it is already writing.""",
   "try": {
    "title": "Measure the queue",
    "minutes": 4,
    "steps": [
     "Run `BackpressureDemo` (or `BackpressureDemoKt`) and note both peaks.",
     "Lower the water marks: add `.childOption(ChannelOption.WRITE_BUFFER_WATER_MARK, new WriteBufferWaterMark(8 * 1024, 16 * 1024))` to the server bootstrap. Predict the new peak with backpressure: about a quarter of the old one?",
     "Run it and explain the number. Where in the handler is writability checked?"
    ],
    "code": {"lang": "java", "title": "BackpressureDemo.java", "src": read(f"{lab}/demo/{P}/BackpressureDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.BackpressureDemo",
             "file": f"{lab}/demo/{P}/BackpressureDemo.java",
             "alt": {"lang": "kotlin", "title": "BackpressureDemo.kt", "src": read(f"{lab}/demo/{K}/BackpressureDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l04.BackpressureDemoKt",
                     "file": f"{lab}/demo/{K}/BackpressureDemo.kt"}},
    "expect": "Without backpressure the peak is in the megabytes and changes every run; with it, about 129,000 bytes. With a 16 KiB high mark the peak only fell to 113,536 bytes in my runs, nowhere near a quarter. The handler checks `isWritable()` in `channelReadComplete`, which runs once after a whole batch of reads, so most of the peak is that one batch arriving before auto-read is switched off. Checking in `channelRead` as well would stop the batch early."
   },
   "refs": [
    {"title": "WriteBufferWaterMark source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/transport/src/main/java/io/netty/channel/WriteBufferWaterMark.java", "kind": "docs"}
   ]
  }
 ],
 "analogy": "The outbound buffer is a bathtub with the drain open and two marks painted on the side. Your handler is the tap. The drain is the socket, and it empties only as fast as the client reads. When the water passes the high mark you turn the tap off (auto-read off), and when it falls below the low mark you turn it back on. Leave the tap running and the bathroom floods. The analogy breaks at the tap: turning it off doesn't waste water. The client's data waits upstream, in the kernel's buffers and the client's own send buffer, and TCP slows the client down for you.",
 "in_your_world": "Card networks and acquirer hosts often speak ISO 8583 over long-lived TCP connections, framed with a short binary length header in front of each message. That is `LengthFieldBasedFrameDecoder` territory, as the worked example shows: a 2-byte length is `(maxLength, 0, 2, 0, 2)`, and a length that counts its own two bytes needs a `lengthAdjustment` of -2. If such a gateway runs on Netty or Vert.x, a missing `release()` shows up weeks later as direct memory that only grows, until buffer allocations fail with an out-of-direct-memory error. Run the gateway's pipeline tests at PARANOID, and give every channel that forwards to a slower system writability-based backpressure.",
 "mistake": "The common leak is a handler that does a little work on a buffer and then forgets whose it is. An audit or logging handler calls `msg.copy()` or `msg.toString(UTF_8)`, passes a copy on, and never releases the original: that is this lesson's lab. The mirror image is a handler that extends `SimpleChannelInboundHandler<ByteBuf>` and also calls `ctx.fireChannelRead(msg)`: the base class releases the buffer when `channelRead0` returns, so the next handler reads freed memory and gets `IllegalReferenceCountException`. Pass the same buffer on with `ChannelInboundHandlerAdapter` and `fireChannelRead(msg)`, or call `ReferenceCountUtil.retain(msg)` before passing it on from a `SimpleChannelInboundHandler`.",
 "compare": {
  "title": "The payment frame encoder and decoder",
  "java": {"title": "PaymentFrameCodec.java", "src": """class PaymentFrameEncoder extends MessageToByteEncoder<PaymentMessage> {
    @Override
    protected void encode(ChannelHandlerContext ctx, PaymentMessage msg, ByteBuf out) {
        byte[] body = msg.body().getBytes(UTF_8);
        out.writeInt(1 + body.length).writeByte(msg.type()).writeBytes(body);
    }
}

class PaymentFrameDecoder extends ByteToMessageDecoder {
    @Override
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) {
        int type = in.readByte();
        out.add(new PaymentMessage(type, in.readCharSequence(in.readableBytes(), UTF_8).toString()));
    }
}"""},
  "kotlin": {"title": "PaymentFrameCodec.kt", "src": """class PaymentFrameEncoder : MessageToByteEncoder<PaymentMessage>() {
    override fun encode(ctx: ChannelHandlerContext, msg: PaymentMessage, out: ByteBuf) {
        val body = msg.body.toByteArray(UTF_8)
        out.writeInt(1 + body.size).writeByte(msg.type).writeBytes(body)
    }
}

class PaymentFrameDecoder : ByteToMessageDecoder() {
    override fun decode(ctx: ChannelHandlerContext, input: ByteBuf, out: MutableList<Any>) {
        val type = input.readByte().toInt()
        out += PaymentMessage(type, input.readCharSequence(input.readableBytes(), UTF_8).toString())
    }
}"""},
  "note": "The runtime behavior is identical; the differences are names and types. Java's decoder parameter is called `in`, which is a keyword in Kotlin, so the Kotlin override renames it (`input`), which overriding allows. `readByte()` returns a `Byte` in Kotlin, and Kotlin never widens it to `Int` implicitly, so you write `.toInt()` where Java widens silently. The `out` list is a Java `List<Object>`, which Kotlin sees as `MutableList<Any>`. Getters such as `isWritable()` and `isAutoRead()` become properties (`isWritable`, `isAutoRead = false`) in Kotlin. Reference counting is the same in both: Kotlin's `use {}` does not help, because `ByteBuf` is not `AutoCloseable`."
 },
 "worked": {
  "title": "Frame an ISO 8583 style link with a 2-byte length",
  "steps": [
   {"say": "An acquirer link sends each message behind a 2-byte big-endian length that counts only the bytes after it. Frames are at most 4,096 bytes. Ask four questions: where is the length, how long is it, what does it count, and do you keep it?",
    "code": "wire:   00 08 | 30 31 30 30 61 75 74 68      (length 8, then \"0100auth\")\noffset: 0               the length starts the frame\nlength: 2 bytes\ncounts: what follows    lengthAdjustment 0\nkeep:   no              initialBytesToStrip 2",
    "lang": "text"},
   {"say": "That gives the decoder's arguments. `LengthFieldPrepender` is the matching encoder: it writes the length in front of every outbound buffer, so the business handler never deals with the header.",
    "code": "ch.pipeline().addLast(\n        new LengthFieldBasedFrameDecoder(4096, 0, 2, 0, 2),   // 1. frame inbound, strip the header\n        new LengthFieldPrepender(2),                          // 2. add the header outbound\n        new Iso8583Codec(),                                   // 3. bytes <-> messages\n        new AuthorizationHandler());",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "ch.pipeline().addLast(\n    LengthFieldBasedFrameDecoder(4096, 0, 2, 0, 2),           // 1. frame inbound, strip the header\n    LengthFieldPrepender(2),                                  // 2. add the header outbound\n    Iso8583Codec(),                                           // 3. bytes <-> messages\n    AuthorizationHandler())"},
   {"say": "A second acquirer counts the 2 header bytes in the length: the same message arrives as `00 0a ...`. The decoder computes the frame size as header end plus the length value plus `lengthAdjustment`, so subtract the 2 bytes the value already includes. The prepender has a flag for the same convention.",
    "code": "new LengthFieldBasedFrameDecoder(4096, 0, 2, -2, 2),   // 10 - 2 = 8 body bytes\nnew LengthFieldPrepender(2, true)                       // write 2 + body length",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "LengthFieldBasedFrameDecoder(4096, 0, 2, -2, 2)         // 10 - 2 = 8 body bytes\nLengthFieldPrepender(2, true)                           // write 2 + body length"},
   {"say": "Prove it with an `EmbeddedChannel` before you connect to anything: write one message out, feed the bytes back in split after the first byte, and expect the original. A wrong adjustment shows up here as a frame that never completes or one that swallows the next message's header.",
    "code": "EmbeddedChannel ch = new EmbeddedChannel(\n        new LengthFieldBasedFrameDecoder(4096, 0, 2, -2, 2), new LengthFieldPrepender(2, true));\nch.writeOutbound(Unpooled.copiedBuffer(\"0100auth\", UTF_8));\nByteBuf wire = ch.readOutbound();                       // 00 0a 30 31 30 30 61 75 74 68\nch.writeInbound(wire.retainedSlice(0, 1));              // half a header: nothing yet\nch.writeInbound(wire.retainedSlice(1, wire.readableBytes() - 1));\nwire.release();\nByteBuf frame = ch.readInbound();                       // \"0100auth\"\nframe.release();",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "val ch = EmbeddedChannel(\n    LengthFieldBasedFrameDecoder(4096, 0, 2, -2, 2), LengthFieldPrepender(2, true))\nch.writeOutbound(Unpooled.copiedBuffer(\"0100auth\", UTF_8))\nval wire = ch.readOutbound<ByteBuf>()                   // 00 0a 30 31 30 30 61 75 74 68\nch.writeInbound(wire.retainedSlice(0, 1))               // half a header: nothing yet\nch.writeInbound(wire.retainedSlice(1, wire.readableBytes() - 1))\nwire.release()\nval frame = ch.readInbound<ByteBuf>()                   // \"0100auth\"\nframe.release()"}
  ]
 },
 "lab": {
  "title": "Write a payment frame codec and find a leak",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/PaymentFrameEncoder.java", f"{lab}/main/{P}/PaymentFrameDecoder.java",
            f"{lab}/main/{P}/PaymentCodec.java", f"{lab}/main/{P}/AuditTap.java", f"{lab}/main/{P}/PaymentMessage.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l04.*'",
  "steps": [
   "Run the tests. All five fail. Read `PaymentMessage.java` for the wire format.",
   "Write `PaymentFrameEncoder.encode`: the length (1 + body bytes) as an `int`, the type as a byte, then the UTF-8 body.",
   "Write `PaymentFrameDecoder.decode`: read the type byte, then the rest as UTF-8 with `readCharSequence`, and add one `PaymentMessage` to `out`. Then `PaymentCodec.handlers`. The first three tests should pass.",
   "Fix `AuditTap` so the buffer that arrived is the one that goes on. The last two tests should pass.",
   "Now make a leak on purpose: in the decoder, read the body with `in.readBytes(in.readableBytes()).toString(UTF_8)`. Run the tests and see which one fails, and why only that one. Put it back."
  ],
  "hints": [
   "The first test prints the bytes as hex: `00000007` is the length, `01` the type, and `617574682d31` is `auth-1` in ASCII.",
   "`in.readCharSequence(n, UTF_8)` decodes in place and moves the reader index. `in.readBytes(n)` allocates a new `ByteBuf`, and nobody releases it.",
   "The AuditTap test fails with a reference count of 1: the buffer that arrived was never released, because a copy went on in its place.",
   "The test class sets PARANOID in `@BeforeAll` and puts the default back in `@AfterAll`. The leak test runs last, so it also catches leaks from the earlier tests."
  ],
  "done_when": "All five tests in `PaymentCodecTest` pass, and you have seen the PARANOID test catch the `readBytes` leak."
 },
 "drill": {
  "title": "Write the backpressure pair from memory",
  "minutes": 4,
  "prompt": "Close this page. In a `ChannelInboundHandlerAdapter` for an echo server, write the two methods that stop reading while the channel isn't writable and start again when it drains. Which default water marks decide when each one fires?",
  "answer": {"lang": "java", "src": """@Override
public void channelRead(ChannelHandlerContext ctx, Object msg) {
    ctx.write(msg);                                   // ownership moves to the write
}

@Override
public void channelReadComplete(ChannelHandlerContext ctx) {
    ctx.flush();
    if (!ctx.channel().isWritable()) ctx.channel().config().setAutoRead(false);
}

@Override
public void channelWritabilityChanged(ChannelHandlerContext ctx) {
    if (ctx.channel().isWritable()) ctx.channel().config().setAutoRead(true);
    ctx.fireChannelWritabilityChanged();
}
// isWritable() turns false above the 64 KiB high water mark, true again below the 32 KiB low mark.""",
             "alt": {"lang": "kotlin", "src": """override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
    ctx.write(msg)                                    // ownership moves to the write
}

override fun channelReadComplete(ctx: ChannelHandlerContext) {
    ctx.flush()
    if (!ctx.channel().isWritable) ctx.channel().config().isAutoRead = false
}

override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
    if (ctx.channel().isWritable) ctx.channel().config().isAutoRead = true
    ctx.fireChannelWritabilityChanged()
}
// isWritable turns false above the 64 KiB high water mark, true again below the 32 KiB low mark."""}}
 },
 "recap": [
  "Frame before you decode. `LengthFieldBasedFrameDecoder(max, offset, length, adjustment, strip)` turns a byte stream into whole frames and rejects frames above `max`.",
  "A `ByteToMessageDecoder` returns without consuming when a frame is incomplete, uses `readerIndex()`-relative access, is never `@Sharable`, and hands frames on as slices, not `readBytes` copies.",
  "A `ByteBuf` has separate reader and writer indexes and a reference count. The last party to touch it releases it; passing it on transfers ownership.",
  "Leaks are found when a tracked buffer is garbage-collected with a count above 0. Run tests at PARANOID with a leak listener and a GC loop, and pair it with a `refCnt() == 0` assertion.",
  "`write` queues in the outbound buffer without limit. Watch `isWritable()` (64 KiB high, 32 KiB low by default) and turn auto-read off while the peer can't keep up.",
  "Close after the last write completes (`ChannelFutureListener.CLOSE`), not right after `flush()`."
 ],
 "quiz": [
  {"q": "`LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)` has received the bytes `00 00 00 03 01 41`. What does it pass to the next handler?",
   "options": ["Nothing yet: the length says 3 bytes follow and only 2 have arrived", "`01 41`", "All six bytes", "It throws, because the frame is shorter than 1024"],
   "answer": 0,
   "why": "The length field says 3 bytes follow; only `01 41` are there. The decoder keeps them in its cumulation and waits for one more byte. 1024 is a maximum, not a required size."},
  {"q": "A handler extends `SimpleChannelInboundHandler<ByteBuf>`, and inside `channelRead0` it calls `ctx.fireChannelRead(msg)` to pass the buffer on. What happens?",
   "options": ["It works: ownership moves to the next handler", "The base class releases the buffer when `channelRead0` returns, so the next handler reads freed memory and fails with `IllegalReferenceCountException`", "Netty copies the buffer for the next handler", "The buffer leaks"],
   "answer": 1,
   "why": "`SimpleChannelInboundHandler` releases the message after `channelRead0`, assuming you consumed it. Passing it on as well means two owners and one release too many. Call `ReferenceCountUtil.retain(msg)` before passing it on, or extend `ChannelInboundHandlerAdapter`."},
  {"q": "Your pipeline tests run at PARANOID and report no leaks. What does that tell you?",
   "options": ["The code has no leaks", "SIMPLE would have found more", "The allocator must be unpooled", "No tracked buffer that was garbage-collected during the run had a count above 0; paths the tests never ran stay invisible"],
   "answer": 3,
   "why": "The detector only sees buffers that were allocated, tracked and collected while the tests ran. A leak on an error path the tests never exercise produces no report. PARANOID tracks more buffers than SIMPLE, not fewer."},
  {"q": "From lesson 3: on which thread does `channelWritabilityChanged` run, even when your writes come from an application thread pool?",
   "options": ["The channel's event loop thread", "A Netty IO thread from a separate pool", "The thread that called `write`", "Whichever thread is free"],
   "answer": 0,
   "why": "Every event of a channel runs on the event loop it is registered with. A write from another thread is queued as a task on that loop, so the outbound buffer and its writability are only ever changed on the loop thread.",
   "from": "io-03"},
  {"q": "A gateway reads authorizations from many terminals and forwards them to a slower card switch over one Netty channel. The switch channel's `isWritable()` turns false. What should the gateway do?",
   "options": ["Keep writing: Netty buffers it", "Close the switch channel and reconnect", "Turn auto-read off on the terminal channels until the switch channel is writable again", "Call `Thread.sleep` in the handler until it is writable"],
   "answer": 2,
   "why": "Stop reading from the producers so the backlog stays in the kernel and in TCP, not in your memory. Writing anyway grows the outbound buffer without limit, and sleeping blocks the event loop for every other channel on it."}
 ],
 "flashcards": [
  {"front": "What do the arguments of `LengthFieldBasedFrameDecoder(1024, 0, 4, 0, 4)` mean?", "back": "Max frame 1024 bytes; the length field is at offset 0 and 4 bytes long; adjustment 0 (it counts only what follows); strip the first 4 bytes before passing the frame on."},
  {"front": "Who releases a `ByteBuf` in a Netty pipeline?", "back": "The party that touches it last. Passing it on with `fireChannelRead` or `write` hands over ownership; consuming it means releasing it."},
  {"front": "Why does `ByteBuf` need `release()` when the JVM has a garbage collector?", "back": "Netty pools direct memory and must get it back as soon as a message is done. The GC frees objects at an unknown later time and can't return pooled chunks."},
  {"front": "`SimpleChannelInboundHandler` vs `ChannelInboundHandlerAdapter`: who releases?", "back": "`SimpleChannelInboundHandler` releases the message after `channelRead0` returns. `ChannelInboundHandlerAdapter` releases nothing; you pass the message on or release it."},
  {"front": "Netty's leak detection levels, in one line each?", "back": "SIMPLE (default): about 1 in 128 buffers, no records. ADVANCED: same sampling, with access records. PARANOID: every buffer, with records; use it in tests."},
  {"front": "When does `channel.isWritable()` turn false, and when true again (defaults)?", "back": "False when the outbound buffer passes the 64 KiB high water mark; true again when it drains below the 32 KiB low mark."},
  {"front": "How do you close a Netty channel without losing the last bytes?", "back": "Close from the last write's future: `ctx.writeAndFlush(last).addListener(ChannelFutureListener.CLOSE)`. `close()` right after `flush()` can drop bytes still in the outbound buffer."}
 ],
 "terms": [
  {"term": "Framing", "plain": "Finding where one message ends and the next begins in a byte stream."},
  {"term": "Length prefix", "plain": "A field before each message that says how many bytes the message has."},
  {"term": "Cumulation", "plain": "The buffer in which a `ByteToMessageDecoder` keeps bytes until a whole frame has arrived."},
  {"term": "Reference count", "plain": "A counter on a `ByteBuf`: retain adds one, release subtracts one, and at zero the memory goes back to the pool."},
  {"term": "Leak detector", "plain": "Netty's `ResourceLeakDetector`, which reports buffers that were garbage-collected without being released."},
  {"term": "Outbound buffer", "plain": "The queue in your process where a channel keeps written messages until the socket can take them."},
  {"term": "Water marks", "plain": "The high and low limits on the outbound buffer that switch `isWritable()` off and on."},
  {"term": "Auto-read", "plain": "Whether the event loop keeps reading a channel; turning it off is how Netty stops `OP_READ`."}
 ],
 "explain_back": {
  "prompt": "Explain why Netty's `ByteBuf` needs `release()` even though the JVM has a garbage collector, and how you would make sure a pipeline doesn't leak.",
  "answer": "Netty allocates direct memory outside the heap so the kernel can use it without a copy, and because that memory is expensive to allocate, Netty pools it: buffers are slices of big chunks that go back to the pool for reuse. The garbage collector would free a buffer object at some unknown later time, which is far too late and can't return a pooled slice anyway. So each buffer has a reference count, and the party that touches it last releases it. In a pipeline, handlers that pass a message on hand over ownership, handlers that consume it release it (`SimpleChannelInboundHandler` does it for you), and Netty releases what you write. To make sure nothing leaks, I'd run the pipeline tests with leak detection at PARANOID, install a leak listener, force garbage collection and an allocation at the end, and assert there were no reports. I'd also assert `refCnt() == 0` on the buffers I pushed in, which catches the common case deterministically."
 },
 "deeper": {
  "minutes": 10,
  "body": """A few `ByteToMessageDecoder` details explain behavior you will see in profiles.

The default cumulator, `MERGE_CUMULATOR`, copies newly read bytes into one growing buffer. `COMPOSITE_CUMULATOR` adds them as components instead and avoids the copy, but the Javadoc warns it may be slower, because reading across component boundaries costs more. The decoder also compacts the cumulation after 16 reads (`discardAfterReads`), so a long-lived connection doesn't keep consumed bytes forever. `setSingleDecode(true)` makes it produce at most one message per read, which matters when you control reading yourself.

That leads to `FlowControlHandler`. With auto-read off you call `ctx.read()` to ask for one more read, but a decoder can still emit many messages from that one read, because one read can contain many frames. Its Javadoc says `FlowControlHandler` \"ensures that only one message per `read()` is sent downstream\". Put it after your decoders when you need strict one-request-at-a-time processing per connection.

On allocators: `io.netty.allocator.type` picks `adaptive` (the 4.2 default), `pooled` or `unpooled`. The adaptive allocator keeps several \"magazines\" of memory, picks one by thread id, and adds magazines when it sees contention. The older pooled allocator keeps per-thread caches, and its `useCacheForAllThreads` setting defaults to false, which suggests that buffers allocated on your own executor threads miss those caches. That last point is an inference from the property name and default, not something this track measured.

Finally, production: leave the level at SIMPLE. It samples 1 buffer in 128, so a leak on a busy path still reaches the logs, while the other 127 buffers pay nothing for tracking."""
 },
 "sources": [
  {"title": "Reference counted objects (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Reference-counted-objects.md"},
  {"title": "ByteToMessageDecoder source and Javadoc, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/codec-base/src/main/java/io/netty/handler/codec/ByteToMessageDecoder.java"},
  {"title": "LengthFieldBasedFrameDecoder source and Javadoc, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/codec-base/src/main/java/io/netty/handler/codec/LengthFieldBasedFrameDecoder.java"},
  {"title": "ResourceLeakDetector source, Netty 4.2", "url": "https://raw.githubusercontent.com/netty/netty/4.2/common/src/main/java/io/netty/util/ResourceLeakDetector.java"},
  {"title": "Netty 4.2 Migration Guide (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md"}
 ]
}

out = ROOT / "content/lessons/io-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
