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


# ---------------------------------------------------------------- opening
OPENING = """Last lesson's post office gave every customer a clerk. Picture it rebuilt. Each customer now gets a box in the wall, with a small light above it. A customer drops a form through the slot whenever it's ready, and the light comes on. Behind the wall sits one clerk, who looks at the lights, serves only the boxes that are lit, and dozes when none are.

That's the plan Blocking IO, threads and the C10K problem ended on, and Java has shipped the parts since Java 1.4: buffers, channels and a selector. Build the echo server on them, and it passes a quick test. Then, under load, it quietly loses bytes, with no exception at all. Leave it idle overnight, and one core runs at 100% while nobody sends a thing.

Both bugs come from small details that look harmless, which is why nearly everyone writes them once. In this lesson, we'll fill a buffer by hand, send bytes that don't all fit, wire up a selector, and switch off the light that never goes out. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with the tray. Everything in `java.nio`, Java's package for non-blocking input and output, moves bytes through a `ByteBuffer`. In the post office, it's the tray behind each box: a fixed number of slots, a cursor that marks the next slot to fill or empty, and a stop line.

In Java, those are three numbers. `capacity` is the tray's size. `position` is the cursor: where the next `put` or `get` happens. `limit` is the stop line: where reading or writing must stop. Most NIO bugs are one of these three numbers being wrong.

A fresh buffer is ready for filling, which we'll call write mode: `position` at 0 and `limit` at `capacity`. Each `put` moves `position` forward. Before you can read what you wrote, `flip()` draws the stop line where filling ended (`limit` becomes `position`) and moves the cursor back to the start (`position` becomes 0). `BufferDemo`, in the Try it below, walks a 16-byte buffer through the whole cycle:

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

After `get(2)` took `he`, where should new bytes go? `compact()` answers that. It slides the unread bytes (`llo`) to the front of the tray and puts the buffer back in write mode right after them, so new data lands behind what you haven't used yet. That's why the content ends as `lloXY`. `clear()` looks similar and does something else: it resets both marks and forgets everything, read or not.

Forget `flip()` and nothing complains. A buffer of 8 with 2 bytes put has `remaining()` 6, so a write sends the 6 bytes after your data, whatever happens to sit in those slots. The buffer will hand over garbage without a murmur, as long as the numbers say so.

There are two kinds of buffer. `allocate` gives a heap buffer, backed by a `byte[]` on the Java heap, the memory where Java keeps its objects. `allocateDirect` gives memory outside the heap. The kernel, the core of the operating system, reads and writes memory by address during a system call (a request a program makes to the kernel), and the garbage collector is allowed to move a `byte[]` around. So the JDK copies a heap buffer through a temporary direct buffer on every channel read and write (`sun.nio.ch.IOUtil` does it).

Direct buffers skip that copy, but the `ByteBuffer` Javadoc says they have "somewhat higher allocation and deallocation costs" and recommends them for large, long-lived buffers. So allocate direct buffers once and reuse them. Netty's allocators, lesson 4, do exactly that.

**A buffer's mode lives in two numbers the compiler can't see. Flip before you read, and compact to keep what's unread.**

A tray is only half the story. The other half is what the kernel does with it."""

# ---------------------------------------------------------------- section 1
S1 = """A **socket** is a program's handle on one end of a network connection, and TCP is the protocol that carries its bytes in order. Every TCP socket has two buffers inside the kernel. The receive buffer holds bytes that arrived from the network and that your program hasn't read yet. The send buffer holds bytes your program wrote that the kernel hasn't delivered yet. In the post office, they're the box's street-side slot and its pick-up shelf: letters waiting to come in, and replies waiting to be collected.

`read` and `write` never touch the network themselves. They copy between your `ByteBuffer` and these two kernel buffers.

A **channel** is `java.nio`'s handle on something bytes move through, such as a socket or a file. Put a `SocketChannel` in non-blocking mode with `configureBlocking(false)`, and its copies stop waiting. They do what the kernel buffers allow right now, and return.

`read(buf)` copies whatever sits in the receive buffer. That can be one byte, half a line, three lines, or nothing at all, in which case it returns 0. It returns -1 when the other side has closed its end.

`write(buf)` is the call that bites. Its Javadoc says a socket channel in non-blocking mode "cannot write any more bytes than are free in the socket's output buffer". When the client reads slowly, the send buffer fills up, and `write` sends part of your buffer, or none of it. That's a **partial write**, a reply that only half fits on the shelf.

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

First we read, appending to whatever the tray already holds. Then we flip, write what the kernel takes, and compact, so the unsent tail moves to the front. After `compact()`, `buf.position() > 0` means bytes are still waiting to go. One run for this track echoed 8 MiB to a client with a 4 KiB receive buffer and counted 8 partial writes. With `clear()` in place of `compact()`, each of them would have dropped bytes.

The read side has a twin rule: one `read` is not one message. TCP is a byte stream. A line sent with one `write` can arrive in three reads, and two lines can arrive in one. Here the post office picture breaks. A real letter arrives whole, but bytes arrive in whatever pieces the network made. Anything beyond a raw echo needs **framing**, a way to tell where one message ends, such as a newline at the end or a length at the front. Lessons 3 and 4 let Netty do it.

One trap lives in the client, too. If a test client writes 8 MiB and only then starts reading, the echo stalls. The server can't send because the client isn't reading, so the server stops reading, so the client's write blocks. Clients of an echo server must read and write at the same time, and the lab's tests use a writer thread for exactly that reason.

**Non-blocking calls move only what fits. Keep the rest per connection, and frame what you read.**

We can read and write without waiting now. What's missing is someone to tell the clerk which boxes to look at."""

# ---------------------------------------------------------------- section 2
S2 = """A `Selector` is the wall of lights. It watches many channels at once. You register each channel with an **interest set**, the events you want to hear about: `OP_ACCEPT` (a new client is waiting), `OP_READ` (bytes arrived) and `OP_WRITE` (there's room to send). Then `select()` blocks until at least one of them is ready.

Each registration is a `SelectionKey`. It carries the interest set, the ready set that the selector fills in, and an attachment, a slot where you keep that connection's state, like a card pinned to the box. Here is the clerk's day:

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

First, `select()` sleeps until a light comes on. Then we walk the list of lit boxes, `selectedKeys()`. A lit accept key means a new customer, so we accept the channel, make it non-blocking and give it a box of its own, with a fresh `Conn` card. Any other key is a box with something to do, and `serve` handles it.

The `it.remove()` line looks like housekeeping, and it isn't. The selector adds keys to the selected set and never takes them out. Leave a key in, and the next pass handles it again, with its old ready set. It's a list of lit boxes that nobody crosses off. `StaleKeyDemo`, in the Try it below, sends exactly one 6-byte message and loops for 300 ms:

```text
remove handled keys=true  loops=7, handled as readable 1 times, bytes read 6
remove handled keys=false loops=7, handled as readable 7 times, bytes read 6
```

Seven visits to a box that held one letter. For an accept key, the same mistake means calling `accept()` again and getting `null` back.

The selector comes with a threading rule, too. Its Javadoc says a selector is safe for use by several threads, but its selected-key set is not. The simple way to obey that is the one every library uses: one thread, one path of work through the program, owns a selector, runs its loop, and does all the work for its channels. Netty, in the next lesson, calls that thread an event loop.

On Linux, `Selector.open()` returns `sun.nio.ch.EPollSelectorImpl`, a wrapper around `epoll`, the Linux system call from lesson 1 that reports ready sockets. On macOS you get a `kqueue` selector. The JDK registers sockets with `epoll` in **level-triggered** mode: as long as a socket is readable or writable, every `select()` reports it again, like a light that stays on while there's mail in the box. The other mode, edge-triggered, is more like a bell that rings once when a letter arrives. A light that stays on is forgiving for reads. For writes, it's the bug in the next section.

**The selector never crosses a box off your list. Remove every key you handle.**"""

# ---------------------------------------------------------------- section 3
S3 = """A socket is writable whenever its send buffer has free space, which is nearly always. Put that next to a level-triggered selector, and you get the classic NIO bug. Register `OP_WRITE` on every connection, and its "room for a reply" light never goes out. `select()` returns at once, reports every idle connection as writable, and the loop goes around again.

`SpinDemo` measures it on one idle connection for 300 ms. One run on a busy 4-core machine printed:

```text
Selector implementation: sun.nio.ch.EPollSelectorImpl
idle 300 ms, interest OP_READ           : 0 wakeups
idle 300 ms, interest OP_READ | OP_WRITE: 374510 wakeups
```

Zero against 374,510, on a connection that sent nothing. That's the clerk walking to a box, finding room for a reply nobody wrote, and walking back, more than a thousand times a millisecond. Under `strace`, a Linux tool that lists a program's system calls, the shape is just as clear: thousands of `epoll_wait` calls and a handful of `epoll_ctl`. On a real server, it shows up as one core at 100% with no traffic at all.

The fix is to register `OP_READ` by default and add `OP_WRITE` only while the connection has unsent bytes. When a write leaves bytes behind, arm it. When a later write drains them, drop it:

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

The `OP_READ` line is the other half of the same idea. When the tray is full because the client reads slowly, stop reading from that client. Its bytes pile up in the kernel's receive buffer, and TCP tells the client how much room is left there (the TCP window). As the window shrinks to zero, the client's own writes stop. That's **backpressure**, a slow receiver slowing the sender down, in two lines. Lesson 4 shows Netty's version of it. In the 8 MiB run from earlier, the server armed `OP_WRITE` only 4 times in 537 selects.

Closing follows the same logic. A client can **half-close** a connection with `shutdownOutput()`: it says it will send nothing more, but it keeps reading. Your `read` then returns -1, the end-of-stream mark (EOF, short for end of file), yet the client still wants the rest of its echo. Close only once nothing is pending.

**A writable socket is the normal case, not news. Ask for OP_WRITE only while bytes are waiting.**"""

# ---------------------------------------------------------------- closing
CLOSING = """We rebuilt the post office around a wall of lights: one thread, a selector, and a tray behind every box. The echo server now keeps the bytes a write couldn't send, crosses every key off its list, closes only when nothing is pending, and asks for the "room for a reply" light only while a reply is waiting.

Now search any selector loop you can find, in your own code or a library's, for `OP_WRITE`. Then find the line that turns it off again. If there isn't one, that loop spins.

Next, we'll hand this loop to Netty. Which of today's rules does a library follow for you, and which one can it never follow on your behalf?"""

L = {
 "id": "io-02",
 "title": "NIO: buffers, channels and selectors",
 "minutes": 35,
 "goal": "By the end you can write a single-threaded NIO server that survives partial reads and writes, keeps unsent bytes, and registers OP_WRITE only while it has something to send.",
 "opening": OPENING,
 "warmup": {
  "q": "An NIO server (one built on `java.nio`, Java's non-blocking IO package) registers every connection for `OP_READ | OP_WRITE`, asking to hear whenever a connection can be read or written, so it can write \"whenever it needs to\". One client connects and sends nothing. What does the server's loop do for the next second?",
  "options": [
   "Sleeps in `select()` until the client sends something",
   "Wakes once, sees nothing to write, and goes back to sleep",
   "Wakes up again and again, hundreds of thousands of times, because the socket is always writable",
   "Throws a `CancelledKeyException`"
  ],
  "answer": 2,
  "why": "A socket with free space in its send buffer counts as writable, and on Linux the selector reports a ready socket on every check for as long as it stays ready, like a light that stays on. So every `select()` returns at once. The demo in this lesson counted 0 wakeups with `OP_READ` alone and 374,510 in 300 ms with `OP_WRITE` added."
 },
 "sections": [
  {
   "h": "The tray behind each box: a ByteBuffer's position and limit",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Three moments of one tray: after writing hello, after flip() the readable bytes run from pos to lim, and compact() slides the unread llo to the front."},
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
    "expect": "With `compact()`: `pos=3 lim=16`, and the content ends as `lloXY`. With `clear()`: `pos=0 lim=16` after the call, `XY` overwrites the first two bytes, and `readable content` prints just `XY`. The unread `llo` was dropped without an error. That's the bug in this lesson's lab."
   }
  },
  {
   "h": "Non-blocking reads and writes move only what fits",
   "body": S1,
   "try": {
    "title": "Count the lost bytes",
    "minutes": 3,
    "steps": [
     "Before you fix anything, run the lab tests with the command below.",
     "Read the failure for `echoesEverything`: how many of the 4,194,304 bytes came back?",
     "Run it twice more. Predict first: will the number be the same?"
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :nio:test --tests 'workbench.nio.l02.*'", "run": ""},
    "expect": "The echo comes back short, by a different amount every run: 73,728 bytes in one run on the busy machine here, around 3.4 million in others. How much gets lost depends on timing: how often the send buffer was full when the server wrote, and when the client's half-close arrived. The idle test fails too, with a wakeup count in the hundreds of thousands."
   },
   "refs": [
    {"title": "WritableByteChannel.write Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/WritableByteChannel.java", "kind": "docs"}
   ]
  },
  {
   "h": "The wall of lights: a Selector tells one thread which channels are ready",
   "body": S2,
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
    "expect": "With `it.remove()`: handled once, 6 bytes read. Without it: handled 7 times in 7 loop passes, still 6 bytes in total. The six extra passes each called `read` and got 0 bytes back, because the key stayed in the selected set and `isReadable()` kept answering from the old ready set."
   },
   "refs": [
    {"title": "Selector Javadoc (JDK 25 source)", "url": "https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/nio/channels/Selector.java", "kind": "docs"}
   ]
  },
  {
   "h": "The light that never goes out: arm OP_WRITE only while bytes wait",
   "body": S3,
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
    "expect": "0 wakeups with `OP_READ`, and hundreds of thousands with `OP_WRITE` added (374,510 and 421,702 for the Java and Kotlin versions on a busy 4-core Linux machine; the exact number depends on processor speed and load). Under `strace` the loop slows down a lot, because strace stops the program on every system call, but the table still shows thousands of `epoll_wait` calls (4,315 in one run) against 5 `epoll_ctl`. On macOS the first line names the kqueue selector."
   }
  }
 ],
 "compare": {
  "title": "The serve step in Java and Kotlin",
  "java": {"title": "serve, Java", "src": serve_java},
  "kotlin": {"title": "serve, Kotlin", "src": serve_kotlin},
  "note": "Both call the same JDK classes, so they behave the same: same partial writes, same level-triggered selector. The differences are on the surface, and they still trip people up. Kotlin has no `|=` for bit flags, so you write `ops = ops or SelectionKey.OP_READ`. Kotlin reads `isReadable()` and `isAcceptable()` as properties (`key.isReadable`), and the attachment is an untyped `Any?` that you cast with `as Conn`, just as Java casts from `Object`. Neither language helps with the buffer's mode: `flip()` and `compact()` change numbers at run time, not types, so neither compiler can stop you from writing a buffer that is still in write mode."
 },
 "worked": {
  "title": "Trace one connection through a partial write",
  "steps": [
   {"say": "The client sends 20 KiB and reads slowly. The server's tray holds 16 KiB. First `select()`: readable. The server reads 16 KiB, flips, and the kernel accepts only 6 KiB of the write.",
    "code": "read 16384      -> pos=16384 lim=16384   (buffer full)\nflip()          -> pos=0     lim=16384\nwrite -> 6144   -> pos=6144  lim=16384   (10240 bytes not sent)\ncompact()       -> pos=10240 lim=16384   (pending: 10240, room: 6144)\ninterest        =  OP_READ | OP_WRITE",
    "lang": "text"},
   {"say": "Second `select()`: readable (the other 4 KiB arrived) and writable (the client read some). The server appends 4 KiB behind the pending bytes, then sends everything it holds.",
    "code": "read 4096       -> pos=14336 lim=16384\nflip()          -> pos=0     lim=14336\nwrite -> 14336  -> pos=14336 lim=14336   (all sent)\ncompact()       -> pos=0     lim=16384   (pending: 0)\ninterest        =  OP_READ               (OP_WRITE dropped: nothing to send)",
    "lang": "text"},
   {"say": "Now the client half-closes while the server still holds bytes. `read` returns -1, so stop reading, but keep `OP_WRITE` until the tail is gone. Close in the pass where `pending` reaches zero.",
    "code": "// 1. remember EOF, don't close yet\nif (key.isReadable() && ch.read(conn.buf) < 0) conn.eof = true;\n// 2. send what we can, keep the rest\nconn.buf.flip();\nif (conn.buf.hasRemaining()) ch.write(conn.buf);\nconn.buf.compact();\n// 3. close only when drained; otherwise ask for exactly what we need\nboolean pending = conn.buf.position() > 0;\nif (conn.eof && !pending) { ch.close(); return; }\nkey.interestOps((conn.eof ? 0 : SelectionKey.OP_READ) | (pending ? SelectionKey.OP_WRITE : 0));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "// 1. remember EOF, don't close yet\nif (key.isReadable && ch.read(conn.buf) < 0) conn.eof = true\n// 2. send what we can, keep the rest\nconn.buf.flip()\nif (conn.buf.hasRemaining()) ch.write(conn.buf)\nconn.buf.compact()\n// 3. close only when drained; otherwise ask for exactly what we need\nval pending = conn.buf.position() > 0\nif (conn.eof && !pending) { ch.close(); return }\nkey.interestOps((if (conn.eof) 0 else SelectionKey.OP_READ) or (if (pending) SelectionKey.OP_WRITE else 0))"},
   {"say": "The lab's version adds one more condition: drop `OP_READ` while the tray has no room left. Without it, a full tray and a readable socket make the same spin as a stray `OP_WRITE`: `select()` says readable, `read()` copies 0 bytes into the full buffer, and the loop goes around again.",
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
  "A non-blocking `read` returns what is there (maybe 0, or -1 at EOF), and `write` may send only part of the buffer. Keep unsent bytes per connection.",
  "One read is not one message. Frame your protocol with a delimiter or a length prefix.",
  "Remove every handled key from `selectedKeys()`. One thread owns a selector and does all the work for its channels.",
  "Linux selectors are level-triggered `epoll`, so `OP_WRITE` on an idle socket fires forever. Arm it only while bytes are pending, drop `OP_READ` while your buffer is full, and close only when drained.",
  "The limit: all of this bookkeeping is yours, and one slow step in `serve` holds up every connection on the selector's thread."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A buffer of capacity 16 holds `hello` after five `put` calls. You call `flip()`, then `get()` twice, then `compact()`. Where are `position` and `limit`?",
   "options": ["position 0, limit 3", "position 3, limit 16", "position 2, limit 5", "position 5, limit 16"],
   "answer": 1,
   "why": "`compact()` moves the 3 unread bytes (`llo`) to the front, sets `position` right after them (3) and `limit` back to `capacity` (16), ready for more filling. Position 2, limit 5 is the state just before `compact()`."},
  {"q": "A non-blocking `ch.write(buf)` returns 4,096, and `buf.remaining()` was 16,384 before the call. What should the server do?",
   "options": ["Call `write` in a loop until everything is sent", "Throw an `IOException`: the client is broken", "Keep the 12,288 bytes with `compact()`, arm `OP_WRITE`, and go back to `select()`", "`clear()` the buffer and read the next message"],
   "answer": 2,
   "why": "The kernel's send buffer is full. Looping would spin (later writes return 0) and hold up every other connection on this thread. Keep the bytes, ask the selector to say when the socket is writable again, and serve other connections meanwhile."},
  {"q": "Your NIO server uses one core at 100% with no traffic. Profiles show the loop thread in `EPollSelectorImpl.doSelect` over and over. What is the most likely cause?",
   "options": ["`OP_WRITE` stays in the interest set of idle connections", "The `ByteBuffer` is a heap buffer, not a direct one", "One selector has too many connections", "The JIT compiled the loop badly"],
   "answer": 0,
   "why": "A level-triggered selector reports a writable socket on every call, and idle sockets are writable. Heap buffers cost a copy per read or write, not a spin, and a busy selector would show real traffic."},
  {"q": "From lesson 1: 5,000 parcel lockers keep connections open, and each sends a 100 ms request every 10 s. How many threads sit blocked in `read()` on a single-selector NIO server, and on a thread-per-connection server?",
   "options": ["0 on the NIO server, about 5,000 on the other", "About 5,000 on both", "50 on both: Little's law decides", "1 on the NIO server, 50 on the other"],
   "answer": 0,
   "why": "NIO reads never block: the one loop thread waits in `select()`, not in `read()`. Thread-per-connection parks one thread per open socket. Little's law gives 50 requests in flight, but that only sets the thread count for thread-per-request designs.",
   "from": "io-01"},
  {"q": "A handler calls `ch.read(buf)` and then parses one message from `buf`. Under load, parsing sometimes fails on a cut-off message. What is wrong?",
   "options": ["The selector is edge-triggered and lost an event", "The buffer must be direct", "`read` must only be called while `OP_WRITE` is armed", "It assumes one read returns one whole message; TCP can split or merge messages, so it needs framing"],
   "answer": 3,
   "why": "TCP delivers a byte stream. One read can hold part of a message or several messages. A delimiter or a length prefix tells the parser when a message is complete; until then, keep the bytes and wait for the next read."}
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
  {"term": "Channel", "plain": "NIO's handle on something bytes move through, such as a socket; it can be made non-blocking."},
  {"term": "Selector", "plain": "An object that waits until one of many registered channels is ready, so one thread can serve them all."},
  {"term": "SelectionKey", "plain": "One channel's registration with a selector: interest set, ready set and an attachment."},
  {"term": "Interest set", "plain": "The events you ask the selector to watch for on a channel: accept, read, write."},
  {"term": "Level-triggered", "plain": "Readiness is reported on every check for as long as it is true, not once when it changes."},
  {"term": "Partial write", "plain": "A non-blocking write that sends only part of the buffer because the kernel's send buffer is full."}
 ],
 "explain_back": {
  "prompt": "Explain to a friend why an NIO echo server must not keep `OP_WRITE` registered all the time, and what it should do after a write that sent only part of its buffer.",
  "answer": "On Linux the selector is level-triggered: it reports a channel for as long as the condition holds, like a light that stays on. A socket is writable whenever its send buffer has room, which is almost always, so a permanent `OP_WRITE` makes every `select()` return at once and the loop burns a core doing nothing. After a partial write, the server should keep the unsent bytes (call `compact()` so they move to the front), register `OP_WRITE` so the selector says when the socket can take more, and go back to `select()` to serve other connections. When a later write drains the buffer, it removes `OP_WRITE` again. While the buffer is full it should also drop `OP_READ`, which pushes back on a client that sends faster than it reads."
 },
 "deeper": {
  "minutes": 10,
  "body": """Level-triggered and edge-triggered are the two ways `epoll` can report readiness. Level-triggered, the default, reports a socket on every `epoll_wait` for as long as it is readable or writable: the light that stays on. Edge-triggered (`EPOLLET`) reports it once, when it changes from not ready to ready, and then stays quiet until the next change: the bell. The JDK's `EPollSelectorImpl` never sets `EPOLLET`, so `Selector` is level-triggered on Linux. That is forgiving for reads (leave bytes unread, and the next `select()` tells you again) and unforgiving for `OP_WRITE`.

Edge-triggered code has the opposite trap: after a notification you must read until `read` returns 0, or you never hear about the leftover bytes. The JDK's virtual-thread poller, which lesson 8 looks at, uses a third mode, `EPOLLONESHOT`: report once, then disarm until the socket is registered again. That fits its job, which is to wake one parked thread once.

Two more details from the JDK source. `EPollSelectorImpl` asks `epoll_wait` for at most `min(fdLimit, 1024)` events per call, so a selector with 10,000 ready sockets needs several calls to see them all. And Netty's NIO transport still carries a guard against selectors that return early with nothing selected: after 512 such returns in a row (`io.netty.selectorAutoRebuildThreshold`), it rebuilds the selector. That is the workaround for the old "epoll spin bug", and the reason Netty counts empty wakeups.

To see the system calls yourself on Linux, run any demo that uses only JDK classes outside Gradle with `strace -f -c -e trace=epoll_wait,epoll_ctl java -cp nio/build/classes/java/demo <class>`. `-c` prints a count per system call when the program exits."""
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
