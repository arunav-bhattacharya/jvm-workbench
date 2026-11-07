import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l02"
K = "kotlin/workbench/nio/l02"
read = lambda p: (ROOT / p).read_text()


def row(y, label, cells, kinds, pos, lim, mode):
    x0, w = 200, 36
    out = [f'<text class="t-s t-code" x="16" y="{y + 22}">{label}</text>']
    for i in range(8):
        out.append(f'<rect class="{kinds[i]}" x="{x0 + i * w}" y="{y}" width="{w}" height="34" rx="4"/>')
        if cells[i]:
            out.append(f'<text class="t t-code" x="{x0 + i * w + w // 2}" y="{y + 22}" text-anchor="middle">{cells[i]}</text>')
    for name, idx, cls in (("pos", pos, "t-a"), ("lim", lim, "t-b")):
        x = x0 + idx * w
        out.append(f'<line class="ln-a" x1="{x}" y1="{y + 36}" x2="{x}" y2="{y + 44}"/>')
        dy = 56 if name == "pos" else 68 if pos == lim else 56
        out.append(f'<text class="t-s {cls}" x="{x}" y="{y + dy}" text-anchor="middle">{name}</text>')
    out.append(f'<text class="t-s t-m" x="510" y="{y + 22}">{mode}</text>')
    return "".join(out)


FIG = (
    '<svg viewBox="0 0 660 290" role="img" aria-label="A ByteBuffer of capacity 8 after put hello, after flip, '
    'and after reading two bytes and calling compact, with the position and limit marks under each row">'
    + row(30, 'put("hello")', list("hello") + ["", "", ""], ["box-a"] * 5 + ["box"] * 3, 5, 8, "write mode")
    + row(120, "flip()", list("hello") + ["", "", ""], ["box-ok"] * 5 + ["box-dim"] * 3, 0, 5, "read mode: 0 to lim")
    + row(210, "get(2); compact()", list("llo") + [""] * 5, ["box-a"] * 3 + ["box"] * 5, 3, 8, "write mode, llo kept")
    + '</svg>'
)

serve_java = """private void serve(SelectionKey key) throws IOException {
    SocketChannel ch = (SocketChannel) key.channel();
    Conn conn = (Conn) key.attachment();
    if (key.isReadable() && ch.read(conn.buf) < 0) conn.eof = true;
    conn.buf.flip();
    if (conn.buf.hasRemaining()) ch.write(conn.buf);
    conn.buf.compact();
    boolean pending = conn.buf.position() > 0;
    if (conn.eof && !pending) { ch.close(); return; }
    int ops = 0;
    if (!conn.eof && conn.buf.hasRemaining()) ops |= SelectionKey.OP_READ;
    if (pending) ops |= SelectionKey.OP_WRITE;
    key.interestOps(ops);
}"""
serve_kotlin = """private fun serve(key: SelectionKey) {
    val ch = key.channel() as SocketChannel
    val conn = key.attachment() as Conn
    if (key.isReadable && ch.read(conn.buf) < 0) conn.eof = true
    conn.buf.flip()
    if (conn.buf.hasRemaining()) ch.write(conn.buf)
    conn.buf.compact()
    val pending = conn.buf.position() > 0
    if (conn.eof && !pending) { ch.close(); return }
    var ops = 0
    if (!conn.eof && conn.buf.hasRemaining()) ops = ops or SelectionKey.OP_READ
    if (pending) ops = ops or SelectionKey.OP_WRITE
    key.interestOps(ops)
}"""

L = {
 "id": "io-02",
 "title": "NIO: buffers, channels and selectors",
 "minutes": 35,
 "goal": "By the end you can write a single-threaded NIO server that survives partial reads and writes, keeps unsent bytes, and registers OP_WRITE only while it has something to send.",
 "warmup": {
  "q": "An NIO server registers every connection for `OP_READ | OP_WRITE` so it can write \"whenever it needs to\". One client connects and sends nothing. What does the server's loop do for the next second?",
  "options": [
   "Sleeps in `select()` until the client sends something",
   "Wakes once, sees nothing to write, and goes back to sleep",
   "Wakes up again and again, hundreds of thousands of times, because the socket is always writable",
   "Throws a `CancelledKeyException`"
  ],
  "answer": 2,
  "why": "A socket with free space in its send buffer is writable, and Linux selectors are level-triggered, so every `select()` reports that idle connection again at once. The demo in this lesson counted 0 wakeups with `OP_READ` alone and 431,909 in 300 ms with `OP_WRITE` added."
 },
 "sections": [
  {
   "h": "A ByteBuffer is a cursor with two marks",
   "body": """Everything in `java.nio` moves bytes through a `ByteBuffer`: a fixed block of memory with three numbers. `capacity` is its size. `position` is where the next `put` or `get` happens. `limit` is where reading or writing must stop. Most NIO bugs are one of these three numbers being wrong.

A fresh buffer is in write mode: `position` 0 and `limit` equal to `capacity`. Each `put` moves `position` forward. Before you can read what you wrote, `flip()` sets `limit` to the current `position` and `position` back to 0. This section's demo walks a 16-byte buffer through the whole cycle:

```text
allocate(16)         pos=0  lim=16 cap=16 remaining=16
put("hello")         pos=5  lim=16 cap=16 remaining=11
flip()               pos=0  lim=5  cap=16 remaining=5
get(2) -> "he"       pos=2  lim=5  cap=16 remaining=3
compact()            pos=3  lim=16 cap=16 remaining=13
put("XY")            pos=5  lim=16 cap=16 remaining=11
flip()               pos=0  lim=5  cap=16 remaining=5
readable content: "lloXY"
```

`compact()` is the call server code needs most. It copies the unread bytes (`llo`) to the front and puts the buffer back in write mode right after them, so new data lands behind what you haven't used yet. `clear()` looks similar and does something else: it resets both marks and forgets everything, read or not.

Forget `flip()` and nothing throws. A buffer of 8 with 2 bytes put has `remaining()` 6, so a write sends the 6 bytes after your data, whatever they happen to be.

There are two kinds of buffer. `allocate` gives a heap buffer backed by a `byte[]`. `allocateDirect` gives memory outside the Java heap. The JDK's Javadoc says direct buffers have "somewhat higher allocation and deallocation costs" and recommends them for large, long-lived buffers used for native IO. They exist because the JDK copies a heap buffer through a temporary direct buffer on every channel read and write (`sun.nio.ch.IOUtil` does it). So allocate direct buffers once and reuse them. Netty's pooled allocators do exactly that for you.""",
   "figure": {"svg": FIG, "caption": "Three moments of one buffer: after writing hello, after flip() the readable bytes run from pos to lim, and compact() keeps the unread llo at the front."},
   "try": {
    "title": "Predict the marks",
    "minutes": 4,
    "steps": [
     "Open `BufferDemo.java` (or `BufferDemo.kt`). Cover the output above and predict `pos` and `lim` after `compact()`.",
     "Run it with the command below and check your prediction.",
     "Change `b.compact()` to `b.clear()` and run it again. What does `readable content` print now, and which bytes are gone?"
    ],
    "code": {"lang": "java", "title": "BufferDemo.java", "src": read(f"{lab}/demo/{P}/BufferDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.BufferDemo",
             "file": f"{lab}/demo/{P}/BufferDemo.java",
             "alt": {"lang": "kotlin", "title": "BufferDemo.kt", "src": read(f"{lab}/demo/{K}/BufferDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.BufferDemoKt",
                     "file": f"{lab}/demo/{K}/BufferDemo.kt"}},
    "expect": "With `compact()`: `pos=3 lim=16`, and the content ends as `lloXY`. With `clear()`: `pos=0 lim=16` after the call, `XY` overwrites the first two bytes, and `readable content` prints just `XY`. The unread `llo` was dropped without an error. That is the bug in this lesson's lab."
   }
  },
  {
   "h": "Non-blocking reads and writes move only what fits",
   "body": """Put a `SocketChannel` in non-blocking mode with `configureBlocking(false)` and its calls stop waiting. They do what the kernel can do right now and return.

`read(buf)` copies whatever sits in the socket's receive buffer. That can be one byte, half a message, three messages, or nothing at all, in which case it returns 0. It returns -1 when the other side has closed its end. `write(buf)` is the call that bites. Its Javadoc says a socket channel in non-blocking mode "cannot write any more bytes than are free in the socket's output buffer". When the client reads slowly, the kernel's send buffer fills, and `write` sends part of your buffer or none of it.

So every connection needs its own buffer for the bytes it hasn't sent yet. The pattern that handles both directions is four lines:

```java
int n = ch.read(buf);    // append whatever arrived, maybe 0 bytes; -1 means the client is done
buf.flip();              // switch to reading what we hold
ch.write(buf);           // send what the kernel accepts, maybe only part of it
buf.compact();           // keep the unsent tail at the front, back to write mode
```

```kotlin
val n = ch.read(buf)     // append whatever arrived, maybe 0 bytes; -1 means the client is done
buf.flip()               // switch to reading what we hold
ch.write(buf)            // send what the kernel accepts, maybe only part of it
buf.compact()            // keep the unsent tail at the front, back to write mode
```

After `compact()`, `buf.position() > 0` means bytes are still waiting. One run for this track echoed 8 MiB to a client with a 4 KiB receive buffer and counted 8 partial writes. With `clear()` in place of `compact()`, each of them would have dropped bytes.

The read side has a twin rule: one `read` is not one message. TCP is a byte stream. A payment message sent with one `write` can arrive in three reads, and two messages can arrive in one. Anything more than raw echo needs framing, such as a length prefix or a delimiter. Lesson 4 builds one with Netty.

One trap lives in the client. If a test client writes 8 MiB and only then starts reading, the echo stalls: the server can't send because the client isn't reading, so the server stops reading, so the client's write blocks. Clients of an echo server must read and write at the same time. The lab's tests use a writer thread for exactly this reason.""",
   "try": {
    "title": "Count the lost bytes",
    "minutes": 3,
    "steps": [
     "Before you fix anything, run the lab tests with the command below.",
     "Read the failure for `echoesEverything`: how many of the 4,194,304 bytes came back?",
     "Run it twice more. Predict first: will the number be the same?"
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :nio:test --tests 'workbench.nio.l02.*'", "run": ""},
    "expect": "The echo comes back short, by a different amount every run (3,469,312, then 3,405,824, then 3,536,896 bytes in three runs here). How much gets lost depends on how often the kernel's send buffer was full at the moment the server wrote, which is timing. The idle test fails too, with a wakeup count in the hundreds of thousands."
   },
   "refs": [
    {"title": "WritableByteChannel.write Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/WritableByteChannel.java", "kind": "docs"}
   ]
  },
  {
   "h": "A Selector tells one thread which channels are ready",
   "body": """A `Selector` watches many channels at once. You register each channel with an interest set, the operations you care about (`OP_ACCEPT`, `OP_READ`, `OP_WRITE`), and `select()` blocks until at least one of them is ready. Each registration is a `SelectionKey`. It carries the interest set, the ready set that the selector fills in, and an attachment where you keep that connection's state.

```java
while (true) {
    selector.select();                                  // sleep until something is ready
    Iterator<SelectionKey> it = selector.selectedKeys().iterator();
    while (it.hasNext()) {
        SelectionKey key = it.next();
        it.remove();                                    // you must remove handled keys yourself
        if (key.isAcceptable()) {
            SocketChannel ch = server.accept();
            ch.configureBlocking(false);
            ch.register(selector, SelectionKey.OP_READ, new Conn());
        } else {
            serve(key);                                 // read, write, update the interest set
        }
    }
}
```

```kotlin
while (true) {
    selector.select()                                   // sleep until something is ready
    val it = selector.selectedKeys().iterator()
    while (it.hasNext()) {
        val key = it.next()
        it.remove()                                     // you must remove handled keys yourself
        if (key.isAcceptable) {
            val ch = server.accept()
            ch.configureBlocking(false)
            ch.register(selector, SelectionKey.OP_READ, Conn())
        } else {
            serve(key)                                  // read, write, update the interest set
        }
    }
}
```

The `it.remove()` line is not optional. The selector adds keys to the selected-key set and never takes them out. Leave a key in and the next pass handles it again with its old ready set. In this section's demo, one 6-byte message was handled as readable 7 times in 300 ms. For an accept key, that means calling `accept()` again and getting `null` back.

The selector also comes with a threading rule. Its Javadoc says a selector is safe for concurrent use, but its selected-key set is not. The simple way to obey that is the one every framework uses: one thread owns a selector, runs its loop, and does all the work for its channels. Netty calls that thread an event loop.

On Linux, `Selector.open()` returns `sun.nio.ch.EPollSelectorImpl`, a wrapper around `epoll`. On macOS you get a `kqueue` selector. The JDK registers sockets with `epoll` in level-triggered mode: as long as a socket is readable or writable, every `select()` reports it again. That one fact is behind the bug in the next section.""",
   "try": {
    "title": "Forget it.remove()",
    "minutes": 3,
    "steps": [
     "Open `StaleKeyDemo.java` (or `StaleKeyDemo.kt`). A client sends exactly one 6-byte message, and the loop runs for 300 ms, once removing handled keys and once not.",
     "Predict how many times each version treats the channel as readable.",
     "Run it with the command below."
    ],
    "code": {"lang": "java", "title": "StaleKeyDemo.java", "src": read(f"{lab}/demo/{P}/StaleKeyDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.StaleKeyDemo",
             "file": f"{lab}/demo/{P}/StaleKeyDemo.java",
             "alt": {"lang": "kotlin", "title": "StaleKeyDemo.kt", "src": read(f"{lab}/demo/{K}/StaleKeyDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.StaleKeyDemoKt",
                     "file": f"{lab}/demo/{K}/StaleKeyDemo.kt"}},
    "expect": "With `it.remove()`: handled once, 6 bytes read. Without it: handled 7 times in 7 loop passes, still 6 bytes in total. The six extra passes each called `read` and got 0 bytes back, because the key stayed in the selected set and `isReadable()` kept returning true from the old ready set."
   },
   "refs": [
    {"title": "Selector Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java", "kind": "docs"}
   ]
  },
  {
   "h": "Arm OP_WRITE only while bytes are waiting",
   "body": """A socket is writable whenever its send buffer has free space, which is nearly always. Combine that with level-triggered `epoll` and you get the classic NIO bug. Register `OP_WRITE` on every connection and `select()` never sleeps again: it returns at once, reports every idle connection as writable, and the loop goes around again.

This section's demo measures it on one idle connection for 300 ms:

```text
Selector implementation: sun.nio.ch.EPollSelectorImpl
idle 300 ms, interest OP_READ           : 0 wakeups
idle 300 ms, interest OP_READ | OP_WRITE: 431909 wakeups
```

Zero against several hundred thousand, on a connection that sent nothing. Under `strace` the shape is just as clear: thousands of `epoll_wait` calls and a handful of `epoll_ctl`. In production it looks like a server at 100% of one core with no traffic.

The rule is to register `OP_READ` by default and add `OP_WRITE` only while the connection has unsent bytes. When a write leaves bytes behind, arm it. When a later write drains them, drop it:

```java
boolean pending = conn.buf.position() > 0;   // after compact(): unsent bytes at the front
int ops = 0;
if (!conn.eof && conn.buf.hasRemaining()) ops |= SelectionKey.OP_READ;   // room left: keep reading
if (pending) ops |= SelectionKey.OP_WRITE;                                // only while bytes wait
key.interestOps(ops);
```

```kotlin
val pending = conn.buf.position() > 0        // after compact(): unsent bytes at the front
var ops = 0
if (!conn.eof && conn.buf.hasRemaining()) ops = ops or SelectionKey.OP_READ   // room left: keep reading
if (pending) ops = ops or SelectionKey.OP_WRITE                                // only while bytes wait
key.interestOps(ops)
```

The `OP_READ` line is the other half of the same idea. When the buffer is full because the client reads slowly, stop reading from that client. Its bytes wait in the kernel, the TCP window shrinks, and the client's own writes slow down. That is backpressure in two lines, and lesson 4 shows Netty's version of it: writability and `AUTO_READ`. In the 8 MiB run mentioned earlier, the server armed `OP_WRITE` only 4 times in 537 selects.

Closing follows the same logic. When `read` returns -1 the client has said it will send nothing more, but it still wants the rest of its echo. Close only once nothing is pending.""",
   "try": {
    "title": "Watch the spin",
    "minutes": 3,
    "steps": [
     "Run `SpinDemo` (or `SpinDemoKt`) with the command below. Predict both numbers first.",
     "On Linux with `strace` installed, run it outside Gradle to count system calls: `strace -f -c -e trace=epoll_wait,epoll_ctl java -cp nio/build/classes/java/demo workbench.nio.l02.SpinDemo`."
    ],
    "code": {"lang": "java", "title": "SpinDemo.java", "src": read(f"{lab}/demo/{P}/SpinDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.SpinDemo",
             "file": f"{lab}/demo/{P}/SpinDemo.java",
             "alt": {"lang": "kotlin", "title": "SpinDemo.kt", "src": read(f"{lab}/demo/{K}/SpinDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l02.SpinDemoKt",
                     "file": f"{lab}/demo/{K}/SpinDemo.kt"}},
    "expect": "0 wakeups with `OP_READ`, and hundreds of thousands with `OP_WRITE` added (431,909 and 534,481 in two runs on my 4-core Linux machine; the exact number depends on CPU speed). Under `strace` the loop slows down a lot, because strace stops the process on every system call, but the table still shows thousands of `epoll_wait` calls (4,315 in my run) against 5 `epoll_ctl`. On macOS the first line names the kqueue selector."
   }
  }
 ],
 "analogy": "Level-triggered readiness is a doorbell that rings for as long as someone stands at the door. `OP_READ` asks \"ring while a visitor is waiting\": you answer, take the parcel, and it stops. `OP_WRITE` asks \"ring while there is room in the outbox\", and the outbox is nearly always empty, so it rings all day and you keep walking to the door for nothing. Ask for that ring only when you have a letter to post. The analogy breaks in one place: `epoll` doesn't ring on its own. Your loop asks it, and level-triggered means it answers yes every time you ask.",
 "in_your_world": "You won't write raw selectors in a Quarkus service, but you will debug their failure modes. A Vert.x or Netty process at 100% of one core with no traffic is often a loop that wakes without work to do. Netty itself fixed one in 4.2.20 (commit 06518dc): a timer due in under half a millisecond rounded the select timeout down to 0, so a loop with a pending timer polled the selector in a circle. Partial reads matter every time you parse a TCP protocol by hand, such as an ISO 8583 link to a card network: a message arrives in several reads, and only its length prefix tells you when you have all of it.",
 "mistake": "The classic mistake is registering `OP_WRITE` together with `OP_READ` \"so the loop can write whenever it needs to\". On a level-triggered selector a socket with buffer space is always writable, so the loop spins at 100% CPU. The second classic is assuming one `write` sends the whole buffer and calling `clear()` after it, which silently drops bytes as soon as a client reads slowly. Write, `compact()`, check `position() > 0`, and arm `OP_WRITE` only then. Close on EOF only after the pending bytes are gone.",
 "compare": {
  "title": "The serve step in Java and Kotlin",
  "java": {"title": "serve, Java", "src": serve_java},
  "kotlin": {"title": "serve, Kotlin", "src": serve_kotlin},
  "note": "Both call the same JDK API, so behavior is identical: same partial writes, same level-triggered selector. The differences are surface ones that still trip people up. Kotlin has no `|=` for bit flags, so you write `ops = ops or SelectionKey.OP_READ`. Kotlin reads `isReadable()` and `isAcceptable()` as properties (`key.isReadable`), and the attachment is an untyped `Any?` that you cast with `as Conn`, just as Java casts from `Object`. Neither language helps you with the buffer's mode: `flip()` and `compact()` are runtime state, not types, so the compiler can't stop you from writing a buffer that is still in write mode."
 },
 "worked": {
  "title": "Trace one connection through a partial write",
  "steps": [
   {"say": "The client sends 20 KiB and reads slowly. The server's buffer holds 16 KiB. First `select()`: readable. The server reads 16 KiB, flips, and the kernel accepts only 6 KiB of the write.",
    "code": "read 16384      -> pos=16384 lim=16384   (buffer full)\nflip()          -> pos=0     lim=16384\nwrite -> 6144   -> pos=6144  lim=16384   (10240 bytes not sent)\ncompact()       -> pos=10240 lim=16384   (pending: 10240, room: 6144)\ninterest        =  OP_READ | OP_WRITE",
    "lang": "text"},
   {"say": "Second `select()`: readable (the other 4 KiB arrived) and writable (the client read some). The server appends 4 KiB behind the pending bytes, then sends everything it holds.",
    "code": "read 4096       -> pos=14336 lim=16384\nflip()          -> pos=0     lim=14336\nwrite -> 14336  -> pos=14336 lim=14336   (all sent)\ncompact()       -> pos=0     lim=16384   (pending: 0)\ninterest        =  OP_READ               (OP_WRITE dropped: nothing to send)",
    "lang": "text"},
   {"say": "Now the client half-closes while the server still holds bytes. `read` returns -1, so stop reading, but keep `OP_WRITE` until the tail is gone. Close in the pass where `pending` reaches zero.",
    "code": "// 1. remember EOF, don't close yet\nif (key.isReadable() && ch.read(conn.buf) < 0) conn.eof = true;\n// 2. send what we can, keep the rest\nconn.buf.flip();\nif (conn.buf.hasRemaining()) ch.write(conn.buf);\nconn.buf.compact();\n// 3. close only when drained; otherwise ask for exactly what we need\nboolean pending = conn.buf.position() > 0;\nif (conn.eof && !pending) { ch.close(); return; }\nkey.interestOps((conn.eof ? 0 : SelectionKey.OP_READ) | (pending ? SelectionKey.OP_WRITE : 0));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "// 1. remember EOF, don't close yet\nif (key.isReadable && ch.read(conn.buf) < 0) conn.eof = true\n// 2. send what we can, keep the rest\nconn.buf.flip()\nif (conn.buf.hasRemaining()) ch.write(conn.buf)\nconn.buf.compact()\n// 3. close only when drained; otherwise ask for exactly what we need\nval pending = conn.buf.position() > 0\nif (conn.eof && !pending) { ch.close(); return }\nkey.interestOps((if (conn.eof) 0 else SelectionKey.OP_READ) or (if (pending) SelectionKey.OP_WRITE else 0))"},
   {"say": "The lab's version adds one more condition: drop `OP_READ` while the buffer has no room left. Without it, a full buffer and a readable socket make the same spin as a stray `OP_WRITE`: `select()` says readable, `read()` copies 0 bytes into the full buffer, and the loop goes around again.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix an NIO echo server that loses bytes and burns a core",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/NioEchoServer.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l02.*'",
  "steps": [
   "Run the tests. All three fail: the 4 MiB echo comes back short, the half-close test loses its tail, and an idle connection wakes the selector hundreds of thousands of times.",
   "In `accept()`, register the new channel for `OP_READ` only.",
   "In `serve()`, replace `clear()` with `compact()` so unsent bytes stay at the front, and only call `write` when the flipped buffer `hasRemaining()`.",
   "Close the channel only when `conn.eof` is true and nothing is pending (`buf.position() == 0` after `compact()`).",
   "End `serve()` by setting the interest set: `OP_READ` while not at EOF and the buffer has room, `OP_WRITE` only while bytes are pending. Run the tests three times."
  ],
  "hints": [
   "After `compact()`, `position()` is exactly the number of bytes still waiting to be sent.",
   "The tests give the client a 4 KiB receive buffer, and the server's sockets an 8 KiB send buffer, so partial writes happen early and often. Your code must not depend on those sizes.",
   "If `idleConnectionDoesNotSpin` still fails, look for any path through `serve()` that returns with `OP_WRITE` still set after the buffer drained.",
   "The half-close test reads slowly on purpose. If it fails with a few kilobytes missing, you close on EOF before the pending bytes are written."
  ],
  "done_when": "All three tests in `NioEchoServerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the serve step from memory",
  "minutes": 5,
  "prompt": "Close the lab. Write `serve(SelectionKey key)` for an echo server whose per-connection state is a `ByteBuffer buf` and a `boolean eof`: read, flip, write, compact, close on EOF only when drained, and set the interest ops. Then check: which line stops the busy spin, and which one applies backpressure?",
  "answer": {"lang": "java", "src": serve_java + "\n// busy spin: OP_WRITE only if pending\n// backpressure: OP_READ only if the buffer has room",
             "alt": {"lang": "kotlin", "src": serve_kotlin + "\n// busy spin: OP_WRITE only if pending\n// backpressure: OP_READ only if the buffer has room"}}
 },
 "recap": [
  "A `ByteBuffer` has `position`, `limit` and `capacity`. `flip()` switches to reading, `compact()` keeps unread bytes and switches back, `clear()` forgets everything.",
  "Non-blocking `read` returns what is there (maybe 0, or -1 at EOF), and `write` may send only part of the buffer. Keep unsent bytes per connection.",
  "One read is not one message. Frame your protocol with a length prefix or a delimiter.",
  "Remove every handled key from `selectedKeys()`. One thread owns a selector and does all the work for its channels.",
  "Linux selectors are level-triggered `epoll`, so `OP_WRITE` on an idle socket fires forever. Arm it only while bytes are pending, drop `OP_READ` while your buffer is full, and close only when drained."
 ],
 "quiz": [
  {"q": "A buffer of capacity 16 holds `hello` after five `put` calls. You call `flip()`, then `get()` twice, then `compact()`. Where are `position` and `limit`?",
   "options": ["position 0, limit 3", "position 3, limit 16", "position 2, limit 5", "position 5, limit 16"],
   "answer": 1,
   "why": "`compact()` moves the 3 unread bytes (`llo`) to the front, sets `position` right after them (3) and `limit` back to `capacity` (16), ready for more writing. Position 2, limit 5 is the state before `compact()`."},
  {"q": "A non-blocking `ch.write(buf)` returns 4,096, and `buf.remaining()` was 16,384 before the call. What should the server do?",
   "options": ["Call `write` in a loop until everything is sent", "Throw an `IOException`: the client is broken", "Keep the 12,288 bytes with `compact()`, arm `OP_WRITE`, and go back to `select()`", "`clear()` the buffer and read the next message"],
   "answer": 2,
   "why": "The kernel's send buffer is full. Looping would spin (later writes return 0) and hold up every other connection on this thread. Keep the bytes, ask the selector to say when the socket is writable again, and serve other connections meanwhile."},
  {"q": "Your NIO server uses one core at 100% with no traffic. Profiles show the loop thread in `EPollSelectorImpl.doSelect` over and over. What is the most likely cause?",
   "options": ["`OP_WRITE` stays in the interest set of idle connections", "The `ByteBuffer` is a heap buffer, not a direct one", "One selector has too many connections", "The JIT compiled the loop badly"],
   "answer": 0,
   "why": "A level-triggered selector reports a writable socket on every call, and idle sockets are writable. Heap buffers cost a copy per IO, not a spin, and a busy selector would show real traffic."},
  {"q": "From lesson 1: 5,000 terminals keep connections open and each sends a 100 ms request every 10 s. How many threads sit blocked in `read()` on a single-selector NIO server, and on a thread-per-connection server?",
   "options": ["0 on the NIO server, about 5,000 on the other", "About 5,000 on both", "50 on both: Little's law decides", "1 on the NIO server, 50 on the other"],
   "answer": 0,
   "why": "NIO reads never block: the one loop thread waits in `select()`, not in `read()`. Thread-per-connection parks one thread per open socket. Little's law gives 50 requests in flight, but that only sets the thread count for thread-per-request designs.",
   "from": "io-01"},
  {"q": "A handler calls `ch.read(buf)` and then parses one payment message from `buf`. Under load, parsing sometimes fails on a truncated message. What is wrong?",
   "options": ["The selector is edge-triggered and lost an event", "The buffer must be direct", "`read` must only be called while `OP_WRITE` is armed", "It assumes one read returns one whole message; TCP can split or merge messages, so it needs framing"],
   "answer": 3,
   "why": "TCP delivers a byte stream. One read can hold part of a message or several messages. A length prefix or delimiter tells the parser when a message is complete; until then, keep the bytes and wait for the next read."}
 ],
 "flashcards": [
  {"front": "What does `flip()` do to a ByteBuffer?", "back": "Sets `limit` to the current `position` and `position` to 0: it switches from writing into the buffer to reading out of it."},
  {"front": "`compact()` vs `clear()`?", "back": "`compact()` moves unread bytes to the front and continues writing after them. `clear()` resets both marks and forgets unread bytes."},
  {"front": "A non-blocking `write(buf)` sent fewer bytes than `buf.remaining()`. Why, and what next?", "back": "The socket's send buffer had less free space. Keep the rest (`compact()`), arm `OP_WRITE`, and write again when the selector says the socket is writable."},
  {"front": "What happens if you never remove keys from `selectedKeys()`?", "back": "They stay selected with their old ready set, so the loop handles the same event on every pass: 7 times in 300 ms for one message in this lesson's demo."},
  {"front": "Why does a permanently registered `OP_WRITE` make a selector spin?", "back": "Linux `epoll` selectors are level-triggered, and a socket with send-buffer space is always writable, so every `select()` returns at once."},
  {"front": "How does an NIO server push back on a client that sends faster than it reads?", "back": "It drops `OP_READ` while its buffer is full. Unread bytes fill the kernel buffer, the TCP window shrinks, and the client's writes slow down."},
  {"front": "Heap or direct ByteBuffer for socket IO?", "back": "Direct, allocated once and reused. The JDK copies a heap buffer through a temporary direct buffer on every channel read or write, and direct buffers are costly to allocate."}
 ],
 "terms": [
  {"term": "ByteBuffer", "plain": "A fixed block of memory with a `position`, a `limit` and a `capacity` that NIO reads into and writes from."},
  {"term": "flip / compact", "plain": "`flip()` switches a buffer from writing to reading; `compact()` keeps unread bytes and switches back."},
  {"term": "Selector", "plain": "An object that waits until one of many registered channels is ready, so one thread can serve them all."},
  {"term": "SelectionKey", "plain": "One channel's registration with a selector: interest set, ready set and an attachment."},
  {"term": "Interest set", "plain": "The operations you ask the selector to watch for on a channel: accept, read, write."},
  {"term": "Level-triggered", "plain": "Readiness is reported on every check for as long as it is true, not once when it changes."},
  {"term": "Partial write", "plain": "A non-blocking write that sends only part of the buffer because the kernel's send buffer is full."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why an NIO echo server must not keep `OP_WRITE` registered all the time, and what it should do after a write that sent only part of its buffer.",
  "answer": "On Linux the selector is level-triggered: it reports a channel as long as the condition holds. A socket is writable whenever its send buffer has space, which is almost always, so a permanent `OP_WRITE` makes every `select()` return immediately and the loop burns a core doing nothing. After a partial write, the server should keep the unsent bytes (call `compact()` so they move to the front), register `OP_WRITE` so the selector says when the socket can take more, and go back to `select()` to serve other connections. When a later write drains the buffer, it removes `OP_WRITE` again. While the buffer is full it should also drop `OP_READ`, which pushes back on a client that sends faster than it reads."
 },
 "deeper": {
  "minutes": 10,
  "body": """Level-triggered and edge-triggered are the two ways `epoll` can report readiness. Level-triggered, the default, reports a socket on every `epoll_wait` for as long as it is readable or writable. Edge-triggered (`EPOLLET`) reports it once, when it changes from not ready to ready, and then stays quiet until the next change. The JDK's `EPollSelectorImpl` never sets `EPOLLET`, so `Selector` is level-triggered on Linux. That is forgiving for reads (if you leave bytes unread, the next `select()` tells you again) and unforgiving for `OP_WRITE`.

Edge-triggered code has the opposite trap: after a notification you must read until `read` returns 0, or you never hear about the leftover bytes. The JDK's virtual-thread poller, which lesson 8 looks at, uses a third mode, `EPOLLONESHOT`: report once, then disarm until the fd is registered again. That fits its job, which is to wake one parked thread once.

Two more details from the JDK source. `EPollSelectorImpl` asks `epoll_wait` for at most `min(fdLimit, 1024)` events per call, so a selector with 10,000 ready sockets needs several calls to see them all. And Netty's NIO transport still carries a guard against selectors that return early with nothing selected: after 512 such returns in a row (`io.netty.selectorAutoRebuildThreshold`), it rebuilds the selector. That is the old \"epoll spin bug\" workaround, and the reason `NioIoHandler` counts empty wakeups.

To see the system calls yourself on Linux, run any demo that only uses JDK classes outside Gradle with `strace -f -c -e trace=epoll_wait,epoll_ctl java -cp nio/build/classes/java/demo <class>`. `-c` prints a count per system call when the process exits."""
 },
 "sources": [
  {"title": "Selector Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java"},
  {"title": "SelectionKey Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/SelectionKey.java"},
  {"title": "ByteBuffer Javadoc template, direct vs non-direct buffers (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/X-Buffer.java.template"},
  {"title": "EPollSelectorImpl (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/linux/classes/sun/nio/ch/EPollSelectorImpl.java"},
  {"title": "Netty commit 06518dc: round up the NIO select timeout to not busy spin", "url": "https://github.com/netty/netty/commit/06518dc"}
 ]
}

out = ROOT / "content/lessons/io-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
