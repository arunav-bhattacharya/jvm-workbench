import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l01"
K = "kotlin/workbench/nio/l01"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Left: four clients, each with its own thread waiting in read. '
    'Right: four clients watched by one selector, and one thread that only runs the ready ones">'
    '<text class="t" x="170" y="28" text-anchor="middle">Thread per connection</text>'
    '<text class="t" x="565" y="28" text-anchor="middle">Event loop</text>'
    + "".join(
        f'<rect class="box" x="20" y="{y}" width="80" height="34" rx="8"/>'
        f'<text class="t-s" x="60" y="{y + 22}" text-anchor="middle">client</text>'
        f'<line class="ln" x1="100" y1="{y + 17}" x2="146" y2="{y + 17}" marker-end="url(#arr)"/>'
        f'<rect class="{"box-a" if i == 1 else "box-dim"}" x="150" y="{y}" width="170" height="34" rx="8"/>'
        f'<text class="t-s{" t-a" if i == 1 else " t-m"}" x="235" y="{y + 22}" text-anchor="middle">'
        f'{"thread: echoing" if i == 1 else "thread: in read()"}</text>'
        f'<rect class="box" x="370" y="{y}" width="80" height="34" rx="8"/>'
        f'<text class="t-s" x="410" y="{y + 22}" text-anchor="middle">client</text>'
        f'<line class="ln-d" x1="450" y1="{y + 17}" x2="486" y2="115" marker-end="url(#arr)"/>'
        for i, y in enumerate([50, 100, 150, 200])
    )
    + '<rect class="box-a" x="490" y="95" width="170" height="40" rx="8"/>'
    '<text class="t-s t-code" x="575" y="120" text-anchor="middle">selector: epoll_wait</text>'
    '<line class="ln-a" x1="575" y1="135" x2="575" y2="171" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="490" y="175" width="170" height="40" rx="8"/>'
    '<text class="t-s" x="575" y="200" text-anchor="middle">1 thread, ready only</text>'
    '<text class="t-s t-bad" x="170" y="258" text-anchor="middle">4 sockets, 4 threads, 3 of them idle</text>'
    '<text class="t-s t-ok" x="565" y="258" text-anchor="middle">4 sockets, 1 thread</text>'
    '</svg>'
)

L = {
 "id": "io-01",
 "title": "Blocking IO, threads and the C10K problem",
 "minutes": 35,
 "goal": "By the end you can say what a blocked socket read costs, use Little's law to count the threads a blocking server needs, and explain why ten thousand mostly idle connections broke thread-per-connection servers.",
 "warmup": {
  "q": "A blocking echo server gives each connection its own platform thread. 2,000 clients connect and then send nothing. How many platform threads does the server hold, and what does `Thread.getState()` say about them?",
  "options": [
   "About 8, one per core, because idle sockets don't need a thread",
   "About 2,000, each reporting RUNNABLE",
   "About 2,000, each reporting WAITING, so they cost nothing",
   "About 200, because the JVM caps platform threads at 200"
  ],
  "answer": 1,
  "why": "Thread-per-connection means one thread per open socket, busy or not, and each one sits inside `read()`. The wait happens in native code, so `getState()` reports RUNNABLE. That is why a thread dump of an idle server looks busy. The demo in this lesson prints it: 2,007 platform threads for 2,000 clients, and RUNNABLE for the blocked handler."
 },
 "sections": [
  {
   "h": "A blocked read holds a whole thread",
   "body": """Here is the core of every classic Java server. One thread accepts connections. Each connection gets a task that reads a line and writes it back.

```java
try (ServerSocket server = new ServerSocket(8080)) {
    while (true) {
        Socket socket = server.accept();          // blocks until a client connects
        pool.execute(() -> echo(socket));         // one task per connection
    }
}

static void echo(Socket socket) {
    try (socket; var in = new BufferedReader(new InputStreamReader(socket.getInputStream(), UTF_8))) {
        var out = socket.getOutputStream();
        String line;
        while ((line = in.readLine()) != null) {  // blocks until the client sends a line
            out.write((line + "\\n").getBytes(UTF_8));
        }
    } catch (IOException e) {
        // the client went away
    }
}
```

```kotlin
ServerSocket(8080).use { server ->
    while (true) {
        val socket = server.accept()              // blocks until a client connects
        pool.execute { echo(socket) }             // one task per connection
    }
}

fun echo(socket: Socket) {
    try {
        socket.use { s ->
            val reader = s.getInputStream().bufferedReader(UTF_8)
            val out = s.getOutputStream()
            while (true) {
                val line = reader.readLine() ?: break   // blocks until the client sends a line
                out.write("$line\\n".toByteArray(UTF_8))
            }
        }
    } catch (e: IOException) {
        // the client went away
    }
}
```

The code is easy to read, and that is its strength. The cost hides in `readLine()`. While the client thinks, types, or sits idle on a keep-alive connection, the thread that called `readLine()` can do nothing else. The kernel keeps it asleep until bytes arrive on that one socket.

Two things surprise people the first time they look.

The thread is not free to keep. A platform thread is an operating system thread with its own stack, and Jetty's documentation puts it at about 1 MiB of native memory. The OS scheduler also has to track every one of them.

And a thread dump hides the waiting. A platform thread blocked in a socket read reports `RUNNABLE`, because the JVM sees it running native code (`SocketDispatcher.read0`). A server with 2,000 idle connections shows 2,000 runnable threads and almost no CPU use.

Vert.x's documentation makes the same point about every blocking API: while the thread waits for a result it can do nothing else, so a lot of concurrency needs a lot of threads. For a blocking server, the question is never how fast one request runs. It is how many threads you can hold, and how many your traffic needs.""",
   "try": {
    "title": "Count the threads",
    "minutes": 4,
    "steps": [
     "Open `ThreadPerConnectionDemo.java` (or the Kotlin twin, `ThreadPerConnectionDemo.kt`). It connects 2,000 clients that never send anything: first to a server with a cached thread pool, then to one with a virtual thread per connection.",
     "Before you run it, write down two predictions: how many platform threads the first server holds, and what `getState()` returns for a handler stuck in `read()`.",
     "Run it from `labs/` with the command below. Then run it again with `-Pargs=5000` added."
    ],
    "code": {"lang": "java", "title": "ThreadPerConnectionDemo.java", "src": read(f"{lab}/demo/{P}/ThreadPerConnectionDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l01.ThreadPerConnectionDemo",
             "file": f"{lab}/demo/{P}/ThreadPerConnectionDemo.java",
             "alt": {"lang": "kotlin", "title": "ThreadPerConnectionDemo.kt", "src": read(f"{lab}/demo/{K}/ThreadPerConnectionDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l01.ThreadPerConnectionDemoKt",
                     "file": f"{lab}/demo/{K}/ThreadPerConnectionDemo.kt"}},
    "expect": "On my 4-core machine with JDK 21 the platform version went from 6 platform threads to 2,007, one per client plus the JVM's own, and the blocked handler reported `RUNNABLE`. The virtual version held the same 2,000 connections with 15 platform threads, and its blocked handler reported `WAITING`. With 5,000 clients the first number became 5,007 and the second stayed at 15."
   }
  },
  {
   "h": "Little's law counts the threads you need",
   "body": """You met Little's law in the executors and virtual threads tracks. The number of requests in a system equals the arrival rate times the time each one spends there: L = λ × W. With thread-per-request, L is also the number of threads you need.

Take an authorization service. At peak it gets 800 requests a second. Each request spends 30 ms in your code and 120 ms waiting for the card issuer. That is 800 × 0.15 s = 120 requests in flight, so 120 busy threads, and a pool of 200 copes. If the issuer slows to 600 ms, the same traffic needs 800 × 0.63 s = 504 threads. Your CPU is no busier. The extra threads are all waiting.

Thread-per-connection is worse than thread-per-request, because it pays for connections, not requests. A connection holds its thread for its whole life, including the idle time between requests. Picture 10,000 point-of-sale terminals that each keep a connection open and send one request every 10 seconds. That is 1,000 requests a second. At 150 ms each, Little's law says 150 are in flight. The thread-per-connection server still needs 10,000 threads, because 9,850 of them sit in `read()` waiting for their terminal's next request.

That gap explains two defaults you may have seen in Tomcat's connector docs. `maxThreads` is 200 and caps simultaneous requests. `maxConnections` is 8,192 and caps open connections. The NIO connector's poller watches the idle sockets with `select()`, so a worker thread is needed only while a request is being processed. Threads follow requests in flight, not open sockets.

Each extra platform thread costs a stack and a slot in the scheduler. A few thousand works, as the demo showed. Tens of thousands is where servers in the late 1990s fell over, and it is still a bad place to be.""",
   "try": {
    "title": "Do the arithmetic before the incident",
    "minutes": 3,
    "steps": [
     "A settlement service reads from Kafka and calls a ledger API: 300 calls a second, 40 ms in your own code, 260 ms waiting for the ledger. How many threads does thread-per-request need?",
     "The ledger has an incident and takes 2 s per call. Traffic stays the same. How many threads now?",
     "Open the lab test `fixedPoolCapsConnections`. Which of your two numbers would a fixed pool of 100 survive, and what would callers see in the other case?"
    ],
    "expect": "300 × 0.3 s = 90 threads normally, and 300 × 2.04 s = 612 threads during the incident. A pool of 100 copes with the first. In the second, tasks queue behind busy threads, latency climbs past every client timeout, and the service looks down while its CPU is idle. The pool ran out of threads that were waiting, not threads that were working."
   },
   "refs": [
    {"title": "Tomcat 11 HTTP connector attributes (docs source)", "url": "https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/http.xml", "kind": "docs"}
   ]
  },
  {
   "h": "C10K: ten thousand clients at once",
   "body": """In 1999 Dan Kegel wrote a page called "The C10K problem". The name is short for ten thousand concurrent clients. His argument was that the hardware of the day could already serve that many connections and the server software could not, because of how it used threads and system calls.

The answer the industry settled on is the one this whole track is about: stop giving each connection a thread. Put many sockets in non-blocking mode and ask the kernel one question: which of these sockets are ready right now? `select` and `poll` were the first system calls for that, and they take the whole list of sockets on every call, which gets slow with thousands of them. Linux added `epoll` and the BSDs and macOS added `kqueue`. Both keep the watched sockets inside the kernel and report only the ones that are ready. One thread can then watch thousands of connections and run code only for those with data.

That one idea has many names on the JVM:

- `java.nio`'s `Selector`, which is `epoll` on Linux and `kqueue` on macOS (lesson 2).
- Netty's event loop: one thread running a selector and your handlers (lessons 3 and 4).
- Vert.x and Quarkus, which run on Netty (lessons 5 and 6).
- Jetty's `ManagedSelector` (lesson 7).
- The JDK's internal poller, which virtual threads use when they block on a socket (lesson 8).

The price is the programming model. A thread that serves thousands of sockets must never block on any one of them. Every read has to return at once with whatever bytes are there, maybe none. Every write has to accept that only part of the buffer went out. Your code becomes a small state machine per connection, called whenever the kernel reports that something happened. The rest of this track is about writing that state machine well, or picking a framework that writes it for you.""",
   "figure": {"svg": FIG, "caption": "Thread per connection parks one thread on every socket. An event loop asks the kernel which sockets are ready and runs only those."},
   "try": {
    "title": "See the waiting threads in a dump",
    "minutes": 4,
    "steps": [
     "Start the demo with 300 clients and hold the connections for 20 seconds: run the command below.",
     "While it holds the platform-thread version, run `jcmd workbench.nio.l01.ThreadPerConnectionDemo Thread.print | grep -c NioSocketImpl.implRead` in a second terminal. `jcmd` accepts the main class name instead of a pid.",
     "Run the same `jcmd` line again once the demo prints the virtual-thread section. Predict the count first."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :nio:demo -Pmain=workbench.nio.l01.ThreadPerConnectionDemo -Pargs='300 20'", "run": ""},
    "expect": "The first count is 300: each handler's stack runs through `NioSocketImpl.implRead` down to `SocketDispatcher.read0`, and its state line says `RUNNABLE`. The second count is 0. `Thread.print` lists platform threads only, and the 300 virtual threads are parked off any thread. Lesson 8 shows how to find them."
   },
   "refs": [
    {"title": "C10k problem (Wikipedia)", "url": "https://en.wikipedia.org/wiki/C10k_problem", "kind": "read"}
   ]
  },
  {
   "h": "Two ways out: fewer threads, or cheaper threads",
   "body": """There are two ways to serve 10,000 connections from one JVM.

The first is the C10K answer: a few threads, each running an event loop over many non-blocking sockets. Netty, Vert.x and Quarkus work this way. It scales very far, and you pay with code that must never block. Call JDBC from an event loop and every other connection on that loop stops until the query returns.

The second arrived in JDK 21: virtual threads (JEP 444). You keep the blocking code from the first section and change the executor.

```java
// echo() stays exactly as it was
ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();
```

```kotlin
// echo() stays exactly as it was
val pool = Executors.newVirtualThreadPerTaskExecutor()
```

The demo showed the effect: 2,000 blocked readers on 15 platform threads. It works because the JDK runs an event loop for you. When a virtual thread's socket read would block, the JDK registers the socket with an internal poller built on `epoll` or `kqueue`, parks the virtual thread, and frees its carrier thread for other work. Lesson 8 opens that poller up.

Neither way makes a single request faster. Non-blocking IO and virtual threads buy concurrency per unit of memory, not latency. A request that waits 120 ms for the card issuer still takes 120 ms. Neither removes the limits behind your service either. If 10,000 virtual threads all want one of 20 database connections, 9,980 of them wait in the pool's queue. The virtual threads track shows how to cap that with a semaphore.

My default for a new blocking service is virtual threads. I'd move to an event-loop framework when measurements say memory per connection or scheduling is the problem, or when the service already lives on one, as every Quarkus service does. Most payment services hit the limits of their downstreams long before either wall.""",
   "try": {
    "title": "Swap the executor, keep the code",
    "minutes": 3,
    "steps": [
     "Finish the lab first, so `BlockingEchoServer` works.",
     "Read the test `virtualThreadsScale`. It passes `Executors.newVirtualThreadPerTaskExecutor()` to the same server class that `idleClientsHoldThreads` runs on a cached pool.",
     "Change its client count from 500 to 2,000 and run only that test with `--tests '*virtualThreadsScale'`. Predict whether the platform-thread assertion still holds."
    ],
    "expect": "It still passes. The platform-thread count grows by a few threads (carriers and poller threads) whether 500 or 2,000 connections are open, because a parked virtual thread holds no OS thread. Put the count back to 500 when you're done."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444", "kind": "read"}
   ]
  }
 ],
 "analogy": "A thread-per-connection server is a restaurant that gives every table its own waiter for the whole evening. The waiter stands by the table while the guests read the menu, eat and talk, and serves nobody else. Forty tables need forty waiters even when only three tables want something. An event loop is one waiter walking the room who stops only at tables where someone raised a hand. The analogy breaks at the kernel: a real waiter has to scan the room, while `epoll` hands the event loop a list of exactly the tables with raised hands.",
 "in_your_world": "Your Quarkus services already avoid thread-per-connection: Vert.x accepts and reads every connection on a few event-loop threads and borrows a worker thread only while a blocking endpoint runs. Thread-per-connection still hides in the code around them: a TCP client to a card network that keeps one reader thread per terminal, an ISO 8583 gateway written years ago, or a Kafka consumer you scaled by adding threads that each block on a 120 ms issuer call. Run Little's law on each one: requests per second times seconds per request gives threads in flight. Then compare that with the threads it actually holds while it waits.",
 "mistake": "The common mistake is sizing a blocking server by CPU: \"we have 8 cores, so 16 threads is plenty.\" That rule is for CPU-bound work. A thread waiting on a socket uses no CPU, so the number comes from Little's law, and for thread-per-connection from the number of open sockets. The opposite mistake usually follows the first outage: raising `maxThreads` to 5,000 to ride out a slow downstream. Now a slow issuer fills 5,000 threads instead of 200, memory climbs, and the issuer receives 5,000 concurrent calls it can't serve either. Size from the traffic you expect, cap concurrency toward each dependency, and make idle connections cheap with an event loop or virtual threads.",
 "compare": {
  "title": "One virtual thread per connection, in both languages",
  "java": {"title": "VirtualEchoServer.java", "src": """try (ServerSocket server = new ServerSocket(8080);
     ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
    while (true) {
        Socket socket = server.accept();
        pool.submit(() -> echo(socket));   // a blocked read parks the virtual thread
    }
}"""},
  "kotlin": {"title": "VirtualEchoServer.kt", "src": """ServerSocket(8080).use { server ->
    Executors.newVirtualThreadPerTaskExecutor().use { pool ->
        while (true) {
            val socket = server.accept()
            pool.submit { echo(socket) }   // a blocked read parks the virtual thread
        }
    }
}"""},
  "note": "The JDK does the work in both: `ExecutorService` is `AutoCloseable` since JDK 19, so Java's try-with-resources and Kotlin's `use` both shut the pool down and wait for running tasks. The difference worth knowing is coroutines. A Kotlin coroutine that calls the blocking `readLine()` does not suspend. It holds its dispatcher thread for the whole wait, so `launch(Dispatchers.IO) { echo(socket) }` is thread-per-connection again, capped by the IO dispatcher's 64 threads. Coroutines only free the thread when the IO call itself suspends, which is what Ktor and Vert.x's Kotlin APIs provide."
 },
 "worked": {
  "title": "Size a terminal gateway with Little's law",
  "steps": [
   {"say": "A gateway keeps one TCP connection per payment terminal: 6,000 terminals. Each terminal sends an authorization every 20 seconds. The gateway spends 15 ms of CPU and 135 ms waiting for the card switch per request. Today it runs one platform thread per connection.",
    "code": "// 1. today: one platform thread per terminal connection\nExecutorService pool = Executors.newCachedThreadPool();\nwhile (true) {\n    Socket terminal = server.accept();\n    pool.execute(() -> serveTerminal(terminal));   // loops: read request, call switch, reply\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "// 1. today: one platform thread per terminal connection\nval pool = Executors.newCachedThreadPool()\nwhile (true) {\n    val terminal = server.accept()\n    pool.execute { serveTerminal(terminal) }       // loops: read request, call switch, reply\n}"},
   {"say": "Apply Little's law to requests, then compare with connections. The gap is the cost of idle connections.",
    "code": "arrival rate   = 6,000 terminals / 20 s       = 300 requests/s\ntime in system = 15 ms + 135 ms              = 0.15 s\nin flight      = 300 x 0.15                  = 45 requests\nthreads held   = one per connection          = 6,000 threads\nidle threads   = 6,000 - 45                  = 5,955 waiting in read()",
    "lang": "text"},
   {"say": "Make idle connections cheap. A virtual thread parked in `read()` holds no OS thread, so the 5,955 idle connections cost a little heap each instead of a platform thread each. The serving code does not change.",
    "code": "// 2. same serveTerminal(), cheap waiting\nExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "// 2. same serveTerminal(), cheap waiting\nval pool = Executors.newVirtualThreadPerTaskExecutor()"},
   {"say": "Now protect the switch. It allows 64 concurrent requests. The old design limited concurrency by accident, through thread count. Virtual threads remove that accident, so put the limit back on purpose, around the call that needs it.",
    "code": "// 3. cap concurrency toward the switch, not the number of connections\nprivate final Semaphore switchSlots = new Semaphore(64);\n\nAuthResponse authorize(AuthRequest req) throws InterruptedException {\n    switchSlots.acquire();\n    try {\n        return cardSwitch.send(req);       // 135 ms\n    } finally {\n        switchSlots.release();\n    }\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "// 3. cap concurrency toward the switch, not the number of connections\nprivate val switchSlots = Semaphore(64)\n\nfun authorize(req: AuthRequest): AuthResponse {\n    switchSlots.acquire()\n    try {\n        return cardSwitch.send(req)        // 135 ms\n    } finally {\n        switchSlots.release()\n    }\n}"}
  ]
 },
 "lab": {
  "title": "Watch a blocking server run out of threads",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/BlockingEchoServer.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l01.*'",
  "steps": [
   "Run the tests once. All four fail: the accept loop and the handler are stubs, so the clients time out after 3 seconds.",
   "Write `acceptLoop()`: while the server socket is open, `accept()` a socket, add it to `open`, and call `handlers.execute(() -> handle(socket))`. Return when `accept()` throws.",
   "Write `handle(Socket)`: increment `inHandler`, wrap the input stream in a UTF-8 `BufferedReader`, and write every line back with `\\n` and a `flush()`. In `finally`, remove the socket from `open` and decrement `inHandler`.",
   "Run the tests until all four pass. Then read `fixedPoolCapsConnections` and `virtualThreadsScale` side by side: the same server code with three executors gives three very different limits."
  ],
  "hints": [
   "`try (socket; BufferedReader in = ...)` closes the socket for you. Since Java 9 you can list an existing effectively final variable in try-with-resources.",
   "`accept()` throws a `SocketException` once `close()` closes the server socket. Treat that as the signal to return.",
   "After `shutdownNow()`, `execute` throws `RejectedExecutionException`. Catch it in the accept loop too, so the acceptor thread ends quietly."
  ],
  "done_when": "All four tests in `BlockingEchoServerTest` pass."
 },
 "drill": {
  "title": "Write a thread-per-connection echo server from memory",
  "minutes": 5,
  "prompt": "Close the lab. Write `static void serve(ServerSocket server, ExecutorService pool)` that accepts forever and echoes each line back on its own task. Then answer: with `Executors.newFixedThreadPool(10)`, what does the 11th idle client see when it sends a line?",
  "answer": {"lang": "java", "src": """static void serve(ServerSocket server, ExecutorService pool) throws IOException {
    while (true) {
        Socket socket = server.accept();
        pool.execute(() -> {
            try (socket; var in = new BufferedReader(new InputStreamReader(socket.getInputStream(), UTF_8))) {
                var out = socket.getOutputStream();
                String line;
                while ((line = in.readLine()) != null) {
                    out.write((line + "\\n").getBytes(UTF_8));
                    out.flush();
                }
            } catch (IOException ignored) { }
        });
    }
}
// The 11th client connects fine: the acceptor accepts it and queues its task.
// Nobody reads its line until one of the first 10 clients disconnects."""},
  "alt": None
 },
 "recap": [
  "A blocking read holds its thread for the whole wait. A platform thread blocked in a socket read even reports `RUNNABLE`.",
  "Little's law, L = λ × W, gives the requests in flight. Thread-per-request needs that many threads; thread-per-connection needs one per open socket, idle or not.",
  "The C10K problem (Dan Kegel, 1999) is serving ten thousand concurrent clients. Thread-per-connection didn't get there.",
  "The fix was readiness notification: non-blocking sockets plus `select`, `poll`, and later `epoll` or `kqueue`, so one thread watches thousands of sockets.",
  "Virtual threads keep blocking code and let the JDK's poller do the watching. Neither they nor event loops make one request faster, and neither removes downstream limits."
 ],
 "quiz": [
  {"q": "A thread-per-connection server has 3,000 clients with open connections. Together they send 600 requests a second, and each request takes 50 ms. How many threads does the server hold?",
   "options": ["30", "600", "About 3,000", "8, one per core"],
   "answer": 2,
   "why": "Little's law gives 600 × 0.05 s = 30 requests in flight, which is what thread-per-request would need. Thread-per-connection keeps a thread on every open socket, so about 3,000. The 30 is the tempting answer, and the difference is the idle time between requests."},
  {"q": "A thread dump of a slow service shows 400 threads in `SocketDispatcher.read0` with state RUNNABLE, and CPU is at 2%. What is going on?",
   "options": ["400 threads are spinning on the CPU", "400 threads are waiting for bytes on their sockets; native blocking reads show up as RUNNABLE", "The JVM is deadlocked", "The garbage collector has paused them"],
   "answer": 1,
   "why": "A platform thread blocked in a socket read is inside native code, so the JVM reports it as RUNNABLE. Low CPU confirms they are waiting, not working. A deadlock would show BLOCKED threads waiting on monitors."},
  {"q": "Which change lets the lab's `BlockingEchoServer` hold 10,000 idle connections without 10,000 platform threads, with no change to `handle()`?",
   "options": ["Pass `Executors.newFixedThreadPool(10_000)`", "Run `handle()` inside `CompletableFuture.supplyAsync`", "Call `socket.setSoTimeout(100)` on every connection", "Pass `Executors.newVirtualThreadPerTaskExecutor()`"],
   "answer": 3,
   "why": "A virtual thread blocked in `read()` parks on the JDK's poller and frees its carrier, so idle connections hold no OS thread. A fixed pool of 10,000 is still 10,000 platform threads. `supplyAsync` runs on the common pool, which has about one thread per core, so most connections would never be served. A short timeout only makes reads fail."},
  {"q": "From the executors track: every thread of a 50-thread pool waits on a payment API that takes 2 s. What is the most this pool can finish per second, however much traffic arrives?",
   "options": ["25", "50", "100", "200"],
   "answer": 0,
   "why": "Turn Little's law around: throughput = threads / time per request = 50 / 2 s = 25 requests a second. Extra traffic only lengthens the queue.",
   "from": "exec-03"},
  {"q": "What do non-blocking IO and virtual threads change for a single request that waits 120 ms for the card issuer?",
   "options": ["It completes in well under 120 ms", "Not its latency: they let many more such requests wait at the same time, at a lower cost per wait", "It no longer needs a database connection", "It gets retried automatically when the issuer is slow"],
   "answer": 1,
   "why": "Both techniques make waiting cheap, so one JVM can keep more requests in flight. The request itself still waits 120 ms for the issuer. Downstream limits such as connection pools stay exactly where they were."}
 ],
 "flashcards": [
  {"front": "What does `getState()` report for a platform thread blocked in a socket `read()`?", "back": "`RUNNABLE`. The wait happens in native code (`SocketDispatcher.read0`), so idle servers look busy in thread dumps."},
  {"front": "Little's law, in one line?", "back": "Requests in the system = arrival rate × time in system (L = λ × W). With thread-per-request, that is the number of threads you need."},
  {"front": "Why does thread-per-connection need more threads than thread-per-request?", "back": "A connection holds its thread while it sits idle between requests. Threads follow open sockets, not requests in flight."},
  {"front": "What is the C10K problem?", "back": "Dan Kegel's 1999 name for serving ten thousand concurrent clients from one server. Thread-per-connection didn't scale there; non-blocking sockets with kernel readiness notification did."},
  {"front": "What does `epoll` (Linux) or `kqueue` (macOS) give a server?", "back": "One call that returns only the sockets that are ready, so one thread can watch thousands of connections."},
  {"front": "Do virtual threads make a request faster?", "back": "No. They make waiting cheap, so more requests can wait at once. A 120 ms issuer call still takes 120 ms."},
  {"front": "2,000 virtual threads blocked in socket reads on a 4-core JDK 21 machine: about how many platform threads?", "back": "About 15 (this lesson's demo): 4 carriers, a few JDK poller threads, and the JVM's own threads."}
 ],
 "terms": [
  {"term": "Blocking IO", "plain": "A read or write that makes the calling thread wait until the operation can finish."},
  {"term": "Thread-per-connection", "plain": "A server design that gives every open socket its own thread for the socket's whole life."},
  {"term": "Thread-per-request", "plain": "A design where a thread is taken from a pool only while a request is being processed."},
  {"term": "Little's law", "plain": "In-flight items = arrival rate × time each item spends in the system."},
  {"term": "C10K", "plain": "Ten thousand concurrent clients on one server; the name of the scaling problem Dan Kegel described in 1999."},
  {"term": "Readiness notification", "plain": "The kernel tells you which sockets can be read or written now (select, poll, epoll, kqueue)."},
  {"term": "Keep-alive connection", "plain": "A connection the client leaves open between requests, so it is idle most of the time."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to raise `maxThreads` from 200 to 4,000 because the card issuer got slow and requests piled up. Explain what those threads were doing, what Little's law says about the incident, and what you would do instead.",
  "answer": "The threads were not working, they were waiting: each one sat in a blocking call to the issuer. Little's law says in-flight requests equal arrival rate times latency, so when the issuer's latency went up the same traffic needed many more threads, and the pool ran out. Raising the limit to 4,000 makes waiting more expensive and sends 4,000 concurrent calls to an issuer that is already struggling. I would keep the pool sized for normal traffic, cap concurrency toward the issuer with a semaphore or bulkhead, add a timeout so callers fail fast, and, if the problem is the cost of waiting threads, move the blocking code to virtual threads or an event loop so waiting stops costing an OS thread."
 },
 "deeper": {
  "minutes": 10,
  "body": """"About 1 MiB per platform thread" needs one detail to be useful. On 64-bit Linux the default stack size (`-Xss`) is 1 MB, and the JVM reserves that much address space per thread. The kernel commits pages only as the stack actually grows, so 2,000 idle threads don't use 2 GB of RAM. They do use real memory for the pages they touched, kernel structures per thread, and a scheduler entry each.

You can see the JVM's view with Native Memory Tracking. Start a JVM with `-XX:NativeMemoryTracking=summary` and run `jcmd <pid> VM.native_memory summary`. The `Thread` section shows how many threads exist and their reserved and committed stack memory. Run it on the demo while it holds 2,000 platform threads and again during the virtual-thread phase.

The limit you hit first in production is often not memory. Containers and hosts cap the number of processes and threads per user or per cgroup (`ulimit -u`, the cgroup `pids.max`). When a JVM can't create a thread it throws `OutOfMemoryError: unable to create native thread`, a confusing name for a thread-count limit.

Thread-per-connection is not always wrong. An internal service with 50 long-lived connections and steady traffic is simpler and faster to debug with one thread per connection, and the thread count never gets near any limit. The problem starts when connection count grows independently of the work, as with keep-alive clients, terminals and mobile apps."""
 },
 "sources": [
  {"title": "Vert.x 5.2.3 core documentation: Don't block me! and Reactor and Multi-Reactor", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc"},
  {"title": "Jetty 12.1 programming guide: threading architecture", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc"},
  {"title": "Tomcat 11 HTTP connector configuration (docs source)", "url": "https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/http.xml"},
  {"title": "C10k problem (Wikipedia)", "url": "https://en.wikipedia.org/wiki/C10k_problem"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"}
 ]
}

# drill answer twin
L["drill"]["answer"]["alt"] = {"lang": "kotlin", "src": """fun serve(server: ServerSocket, pool: ExecutorService) {
    while (true) {
        val socket = server.accept()
        pool.execute {
            try {
                socket.use { s ->
                    val reader = s.getInputStream().bufferedReader(UTF_8)
                    val out = s.getOutputStream()
                    while (true) {
                        val line = reader.readLine() ?: break
                        out.write("$line\\n".toByteArray(UTF_8))
                        out.flush()
                    }
                }
            } catch (_: IOException) {
            }
        }
    }
}
// The 11th client connects fine: the acceptor accepts it and queues its task.
// Nobody reads its line until one of the first 10 clients disconnects."""}
del L["drill"]["alt"]

out = ROOT / "content/lessons/io-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
