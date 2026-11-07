import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l08"
KP = "kotlin/workbench/executors/l08"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l08.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l08.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

def rect(cls, x, y, w, h, label, tcls="t t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
            f'<text class="{tcls}" x="{x + w / 2:.0f}" y="{y + h / 2 + 5:.0f}" text-anchor="middle">{label}</text>')

SVG = ('<svg viewBox="0 0 680 300" role="img" aria-label="Work stealing: worker 1 pushes and pops small tasks at the top of its own deque, while idle worker 2 steals the oldest and largest task from the bottom">'
       '<text class="t" x="170" y="24" text-anchor="middle">worker 1</text>'
       '<text class="t" x="530" y="24" text-anchor="middle">worker 2</text>'
       + rect("box-ok", 80, 36, 180, 36, "runs [1.75M, 2M)")
       + '<text class="t-s t-m" x="170" y="94" text-anchor="middle">its deque, newest on top</text>'
       + rect("box", 80, 104, 180, 36, "[1.5M, 1.75M)")
       + rect("box", 80, 148, 180, 36, "[1M, 1.5M)")
       + rect("box-a", 80, 192, 180, 36, "[0, 1M)")
       + '<line class="ln" x1="80" y1="100" x2="80" y2="232"/><line class="ln" x1="260" y1="100" x2="260" y2="232"/>'
       + '<text class="t-s" x="40" y="118" text-anchor="middle">fork</text>'
       + '<line class="ln-a" x1="40" y1="124" x2="76" y2="124" marker-end="url(#arr)"/>'
       + '<text class="t-s" x="40" y="148" text-anchor="middle">pop</text>'
       + '<line class="ln-a" x1="76" y1="132" x2="40" y2="154" marker-end="url(#arr)"/>'
       + '<text class="t-s t-m" x="170" y="252" text-anchor="middle">oldest task at the bottom</text>'
       + '<text class="t-s t-m" x="170" y="268" text-anchor="middle">is the biggest piece</text>'
       + rect("box-dim", 440, 104, 180, 36, "deque empty", "t")
       + rect("box-a", 440, 192, 180, 36, "steals [0, 1M)")
       + '<line class="ln-a" x1="262" y1="210" x2="436" y2="210" marker-end="url(#arr)"/>'
       + '<text class="t-s" x="350" y="200" text-anchor="middle">steal from the bottom</text>'
       + '<text class="t-s t-m" x="530" y="252" text-anchor="middle">then splits it on its own deque:</text>'
       + '<text class="t-s t-m" x="530" y="268" text-anchor="middle">one steal brings lots of work</text>'
       + '</svg>')

L = {
 "id": "exec-08",
 "title": "ForkJoinPool, work stealing and parallel streams",
 "minutes": 35,
 "goal": "By the end you can write a RecursiveTask that really runs in parallel, explain how work stealing keeps the workers busy, and say when a parallel stream helps and when it starves the whole JVM.",
 "warmup": {
  "q": "In a `RecursiveTask`, `compute()` splits the range into `left` and `right`, then runs `left.fork(); long l = left.join(); long r = right.compute(); return l + r;`. On a 4-worker pool, how much faster than one thread is it?",
  "options": [
   "About 4 times faster, because every split forks a task",
   "About 2 times faster, because only the top split runs in parallel",
   "About the same speed as one thread",
   "It deadlocks, because a worker joins its own task"
  ],
  "answer": 2,
  "why": "`join()` right after `fork()` waits for the left half before the right half starts, so the two halves of every split run one after the other. The worker usually just pops the task it forked and runs it itself, which is legal and doesn't deadlock. Put `right.compute()` between the fork and the join and the same code gets close to 4 times faster."
 },
 "sections": [
  {
   "h": "RecursiveTask: split until the piece is small, then loop",
   "body": "`ForkJoinPool` (JDK 7) is a pool built for one shape of work: a big CPU job that splits itself into smaller jobs of the same kind. You describe the job as a `RecursiveTask<V>`, which returns a value, or a `RecursiveAction`, which doesn't. Both have one method to write, `compute()`, and it nearly always has this shape:\n\n```java\nclass SumTask extends RecursiveTask<Long> {\n    static final int THRESHOLD = 10_000;\n    final long[] a; final int from, to;\n\n    SumTask(long[] a, int from, int to) { this.a = a; this.from = from; this.to = to; }\n\n    @Override\n    protected Long compute() {\n        if (to - from <= THRESHOLD) {                   // 1. small enough: just loop\n            long sum = 0;\n            for (int i = from; i < to; i++) sum += a[i];\n            return sum;\n        }\n        int mid = (from + to) >>> 1;                    // 2. split\n        SumTask left = new SumTask(a, from, mid), right = new SumTask(a, mid, to);\n        left.fork();                                    // 3. let another worker take the left half\n        long r = right.compute();                       // 4. do the right half here\n        return left.join() + r;                         // 5. then collect the left half\n    }\n}\n\nlong total = ForkJoinPool.commonPool().invoke(new SumTask(amounts, 0, amounts.length));\n```\n\n```kotlin\nclass SumTask(val a: LongArray, val from: Int, val to: Int) : RecursiveTask<Long>() {\n    override fun compute(): Long {\n        if (to - from <= THRESHOLD) {                   // 1. small enough: just loop\n            var sum = 0L\n            for (i in from until to) sum += a[i]\n            return sum\n        }\n        val mid = (from + to) ushr 1                    // 2. split\n        val left = SumTask(a, from, mid)\n        val right = SumTask(a, mid, to)\n        left.fork()                                     // 3. let another worker take the left half\n        val r = right.compute()                         // 4. do the right half here\n        return left.join() + r                          // 5. then collect the left half\n    }\n\n    companion object { const val THRESHOLD = 10_000 }\n}\n\nval total = ForkJoinPool.commonPool().invoke(SumTask(amounts, 0, amounts.size))\n```\n\nThe threshold is the one number you have to choose. Too big, and there are only a few pieces, so some workers sit idle at the end. Too small, and the cost of creating and scheduling task objects eats the gain. The `ForkJoinTask` Javadoc gives a very rough rule: a task should do more than 100 and less than 10,000 basic computational steps. Then measure.\n\nForkJoin tasks are for CPU work on data you already have in memory: summing a ledger, sorting, searching, transforming a big array. They should not block on I/O or locks, for reasons the last section shows.",
   "try": {
    "title": "Change the threshold",
    "minutes": 4,
    "steps": [
     "Run `WorkStealingDemo`. It totals fees over 2,000,000 ledger entries, first on one thread, then on a `ForkJoinPool` with 4 workers. Note the speed-up and how many leaves each worker ran.",
     "Run it with `-Pargs=\"right 500\"`, then with `-Pargs=\"right 1000000\"`. Before each run, predict the number of leaves and how many workers will have any."
    ],
    "code": demo("WorkStealingDemo"),
    "expect": "With the default threshold of 50,000, all four workers run some of the 64 leaves, and the pool finishes about 3 to 4 times faster than one thread if your machine has 4 free cores. With 500 there are 4,096 leaves and it is still fast, a little slower from the extra tasks. With 1,000,000 there are only 2 leaves, so only 2 workers ever get work and the speed-up drops to about 2."
   },
   "refs": [
    {"title": "ForkJoinTask (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ForkJoinTask.html", "kind": "docs"}
   ]
  },
  {
   "h": "Work stealing, and why fork, compute, join is the only good order",
   "body": "A `ThreadPoolExecutor` has one shared queue. A `ForkJoinPool` gives every worker its own double-ended queue, a deque. `fork()` pushes the task onto the top of the current worker's deque. The worker also pops from the top, so it always works on the task it forked most recently: the smallest one, whose data is still in its cache.\n\nA worker whose deque is empty becomes a thief. It picks another worker and takes the task at the **bottom** of that worker's deque. That is the oldest task, forked highest up in the recursion, so it is the biggest piece of work available. The thief splits it on its own deque and stays busy for a long time. That's why `WorkStealingDemo` reports only a handful of steals for 64 leaves.\n\n`join()` doesn't simply park the thread. If the task is still on the worker's own deque, the worker pops it and runs it. If a thief took it, the worker helps by running other pending tasks while it waits. A fork/join pool doesn't need a spare thread for every task that is waiting on another.\n\nNow the order. Fork one half, compute the other on this thread, and only then join:\n\n```java\nleft.fork();                    // the left half becomes stealable\nlong r = right.compute();       // this thread works while a thief can take the left half\nreturn left.join() + r;\n```\n\n```kotlin\nleft.fork()                     // the left half becomes stealable\nval r = right.compute()         // this thread works while a thief can take the left half\nreturn left.join() + r\n```\n\nSwap the last two steps, `left.fork(); left.join(); right.compute()`, and the worker waits for the left half before it even starts the right one. The two halves of every split run one after the other. `left.compute() + right.compute()` is the same thing written honestly: sequential code with extra objects. Both still give the right total, which is why the bug survives code review. `invokeAll(left, right)` is the library's shortcut for the correct order.",
   "figure": {"svg": SVG, "caption": "Each worker pushes and pops at the top of its own deque. An idle worker steals from the bottom, where the oldest and biggest task waits."},
   "try": {
    "title": "Join too early",
    "minutes": 3,
    "steps": [
     "Run `WorkStealingDemo` with `-Pargs=wrong`. It joins the left half before computing the right one.",
     "Compare the time with the one-thread line, and look at how the leaves are spread. Why can leaves land on two workers when nothing runs in parallel?"
    ],
    "code": demo("WorkStealingDemo"),
    "expect": "The wrong order takes about as long as one thread, sometimes a little longer. Most leaves run on one worker, with a few on a second one: sometimes a thief steals the forked half in the moment between `fork` and `join`, but then the first worker just waits for it, so the work still happens one piece at a time."
   }
  },
  {
   "h": "Parallel streams run on the common pool, along with everything else",
   "body": "`list.parallelStream()` splits its source into pieces and runs them as fork/join tasks on `ForkJoinPool.commonPool()`. The calling thread takes part too: in `SharedStateDemo`, `main` shows up next to the common pool workers.\n\nThe common pool has `availableProcessors() - 1` threads by default (you can change it with `-Djava.util.concurrent.ForkJoinPool.common.parallelism`). It is one pool for the whole JVM. Every parallel stream uses it, every `CompletableFuture` async method without an executor uses it (lesson 6 of this track), and from JDK 25 so does scheduling on the common pool (lesson 5). Whatever runs there competes with all of that.\n\nThree mistakes cover most parallel stream bugs.\n\n- Writing to shared state races. `forEach(p -> list.add(p))` on an `ArrayList`, or `forEach(x -> total[0] += x)`, runs the same read-modify-write races as any other threads. The demo loses about half the ids, and the sum comes out wrong by billions. Let the stream build the result: `toList()`, `collect(...)`, `sum()`, `reduce(...)`. Each thread works on its own piece, and the stream combines the pieces at the end.\n- Order isn't kept. `forEach` on a parallel stream runs in whatever order the threads get to the elements. `toList()` and `forEachOrdered` keep the source order, at some cost.\n- Too little work makes it slower. Splitting, scheduling and combining cost time. A stream of 1,000 cheap elements is faster sequential. Sources that split badly, such as a `LinkedList`, `Stream.iterate` or lines from a file, give the pool little to share out. Measure both versions, ideally with JMH (the OpenJDK harness for microbenchmarks), before you keep `parallel()`.",
   "try": {
    "title": "Collect from many threads",
    "minutes": 3,
    "steps": [
     "Run `SharedStateDemo`. Before you do, predict the size of the shared list and whether the shared sum is right.",
     "Run it twice more. Which numbers change between runs, and which never do?"
    ],
    "code": demo("SharedStateDemo"),
    "expect": "The shared `ArrayList` ends up with fewer than 100,000 ids, out of order (one run here kept 52,325), or the stream throws `ArrayIndexOutOfBoundsException`. The shared `long[]` sum is wrong. `toList()` always has all 100,000 in order and `mapToLong().sum()` always prints 4,999,950,000. The thread list shows `main` plus the common pool workers."
   },
   "refs": [
    {"title": "java.util.stream package: parallelism and side effects (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html", "kind": "docs"}
   ]
  },
  {
   "h": "Blocking calls starve the common pool",
   "body": "A `ForkJoinPool` tries to keep about `parallelism` threads running. When one of them blocks in `Thread.sleep`, a socket read or a JDBC call, the pool normally doesn't know, and that thread is simply gone until the call returns. With 7 workers on an 8-core pod, seven slow issuer lookups in a parallel stream take every common pool thread in the JVM.\n\n`StarvationDemo` runs four rounds of 300 ms lookups in a parallel stream. As soon as all the threads are busy, another thread submits a task that should take microseconds, through `supplyAsync` with no executor. It waits about 1.2 seconds, until the lookups are nearly done. In a service, that tiny task is somebody else's request.\n\nThe fix is to keep I/O off the common pool. Run blocking calls on an executor built for waiting: a bounded pool sized for the downstream, or virtual threads, which the next track covers. Then combine the results with `CompletableFuture`. In the demo's `io` mode, the lookups finish in about 300 ms and the tiny task waits about 2 ms.\n\nThere is also a patch for code you can't move. `ForkJoinPool.managedBlock(blocker)` tells the pool \"this worker is about to block\", and the pool may start a spare thread to keep its parallelism up. `CompletableFuture` uses it internally when a pool thread calls `join()`. In the demo's `managed` mode, spare workers appear (with names like `commonPool-worker-10`) and both numbers look good again. It is still a patch: every blocked call costs a whole platform thread, and the spares are capped.\n\nYou may read that a parallel stream started inside `customPool.submit(...)` runs on `customPool`. It does today, but it is how the implementation behaves, not something the specification promises. Don't build on it.",
   "try": {
    "title": "Starve the common pool",
    "minutes": 4,
    "steps": [
     "Run `StarvationDemo`. Note how long the tiny task waits and which thread finally runs it.",
     "Run it with `-Pargs=io`, then with `-Pargs=managed`. Predict each time: how long do all the lookups take, and how long does the tiny task wait?"
    ],
    "code": demo("StarvationDemo"),
    "expect": "In the default mode the lookups take about 1.2 s (four rounds of 300 ms on the common pool plus `main`), and the tiny task waits about as long, because every common pool thread is asleep. With `io` the lookups take about 300 ms and the tiny task waits a few milliseconds. With `managed` the pool adds spare workers, so both drop again, and the tiny task runs on one of the extra threads."
   }
  }
 ],
 "analogy": "A fork/join pool is a team splitting a stack of 2,000 invoices to check. Each clerk keeps a personal pile. When you split your pile, you put half on top of it and keep working on the other half yourself. A clerk with nothing to do walks over and takes the bottom of somebody else's pile, which is the biggest bundle, so nobody has to walk over often. The analogy breaks when a clerk picks up the phone to a supplier for ten minutes: in an office you'd notice and share out the pile, but the pool usually can't tell a thread is waiting, so that clerk's desk just stands empty.",
 "in_your_world": "Good fork/join work in a payment service is CPU work on data already in memory: totalling fees over a day's ledger extract, building a settlement file, deduplicating a batch of idempotency keys, sorting a big reconciliation set. Bad work is anything that calls out: an issuer lookup, a database query or a Kafka send inside a `parallelStream()`. On an 8-core Quarkus pod that has 7 common pool threads shared by the whole service, and the stall shows up as unrelated `CompletableFuture` timeouts somewhere else. When you do turn on `parallel()`, check the container's CPU limit, because `availableProcessors()` follows it and a 2-CPU pod gets a common pool of one worker.",
 "mistake": "The most common mistake is putting blocking calls in a parallel stream: `ids.parallelStream().map(client::fetch).toList()`. It looks like a free speed-up and it is one in a laptop test, where nothing else needs the common pool. In production the calls hold the common pool's few threads, and every parallel stream and every executor-less `CompletableFuture` in the JVM waits behind them. People reach for it because `parallelStream()` is the shortest way to say \"do these at once\". For I/O, say it with an executor: `supplyAsync(() -> client.fetch(id), io)` for each id, then join them all at the edge.",
 "compare": {
  "title": "Divide and conquer: RecursiveTask vs coroutines",
  "java": {"title": "CountOver.java (ForkJoinPool)", "src": "class CountOver extends RecursiveTask<Integer> {\n    final long[] a; final long limit; final int from, to;\n\n    CountOver(long[] a, long limit, int from, int to) {\n        this.a = a; this.limit = limit; this.from = from; this.to = to;\n    }\n\n    @Override\n    protected Integer compute() {\n        if (to - from <= 10_000) {\n            int n = 0;\n            for (int i = from; i < to; i++) if (a[i] > limit) n++;\n            return n;\n        }\n        int mid = (from + to) >>> 1;\n        CountOver left = new CountOver(a, limit, from, mid);\n        CountOver right = new CountOver(a, limit, mid, to);\n        left.fork();                       // stealable\n        int r = right.compute();           // work here\n        return left.join() + r;            // then collect\n    }\n}\n\nint flagged = ForkJoinPool.commonPool().invoke(new CountOver(amounts, 500_000, 0, amounts.length));"},
  "kotlin": {"title": "CountOver.kt (kotlinx.coroutines)", "src": "suspend fun countOver(a: LongArray, limit: Long, from: Int, to: Int): Int =\n    if (to - from <= 10_000) {\n        (from until to).count { a[it] > limit }\n    } else coroutineScope {\n        val mid = (from + to) ushr 1\n        val left = async { countOver(a, limit, from, mid) }   // like fork()\n        val right = countOver(a, limit, mid, to)              // like compute()\n        left.await() + right                                  // like join()\n    }\n\nval flagged = runBlocking(Dispatchers.Default) { countOver(amounts, 500_000, 0, amounts.size) }"},
  "note": "Kotlin can extend `RecursiveTask` exactly like Java (the Kotlin `WorkStealingDemo` does). The coroutine version keeps the same shape and the same order rule: start the left half with `async`, compute the right half in place, then `await`. Two things differ. `Dispatchers.Default` is kotlinx.coroutines' own shared thread pool, sized to the number of cores (at least two); it is not the common `ForkJoinPool`, so it doesn't compete with parallel streams. And `await()` suspends the coroutine instead of helping with other tasks, so the thread goes back to the dispatcher. Blocking calls are just as wrong on `Dispatchers.Default` as on the common pool; they belong on `Dispatchers.IO`."
 },
 "worked": {
  "title": "Speed up a nightly fee report without breaking it",
  "steps": [
   {"say": "The report totals fees per merchant over 4 million payments. Someone made it parallel. Before reading on, find what breaks.",
    "code": "Map<String, Long> feesByMerchant = new HashMap<>();\npayments.parallelStream().forEach(p ->\n        feesByMerchant.merge(p.merchant(), fee(p), Long::sum));   // one HashMap, many threads", "lang": "java",
    "alt_code": "val feesByMerchant = HashMap<String, Long>()\npayments.parallelStream().forEach { p ->\n    feesByMerchant.merge(p.merchant, fee(p), Long::plus)       // one HashMap, many threads\n}", "alt_lang": "kotlin"},
   {"say": "Many threads call `merge` on one `HashMap`. That loses updates, and a resize under concurrent writes can corrupt the map. Let the stream build the result instead: with `groupingBy`, each thread fills its own partial map and the stream merges them at the end.",
    "code": "// 1. CPU work only, and the stream owns the result\nMap<String, Long> feesByMerchant = payments.parallelStream()\n        .collect(Collectors.groupingBy(Payment::merchant, Collectors.summingLong(this::fee)));", "lang": "java",
    "alt_code": "// 1. CPU work only, and the stream owns the result\nval feesByMerchant: Map<String, Long> = payments.parallelStream()\n    .collect(Collectors.groupingBy({ it.merchant }, Collectors.summingLong(::fee)))", "alt_lang": "kotlin"},
   {"say": "Next someone wants merchant names in the report, from a service that takes 20 ms per call. Calling it inside the parallel stream would block the common pool for 4 million calls. There are only about 3,000 merchants, so look the names up after the aggregation, once each, on an IO pool.",
    "code": "// 2. IO goes to a pool built for waiting, once per merchant\nMap<String, CompletableFuture<String>> names = feesByMerchant.keySet().stream()\n        .collect(Collectors.toMap(id -> id, id -> CompletableFuture.supplyAsync(() -> merchants.name(id), io)));\n// 3. wait at the edge: the report job's own thread may block\nnames.forEach((id, name) -> report.line(name.join(), feesByMerchant.get(id)));", "lang": "java",
    "alt_code": "// 2. IO goes to a pool built for waiting, once per merchant\nval names = feesByMerchant.keys.associateWith { id ->\n    CompletableFuture.supplyAsync({ merchants.name(id) }, io)\n}\n// 3. wait at the edge: the report job's own thread may block\nnames.forEach { (id, name) -> report.line(name.join(), feesByMerchant.getValue(id)) }", "alt_lang": "kotlin"},
   {"say": "Last question: is `parallel()` worth keeping? Time both versions on production-sized data, with JMH or at least a few warm runs. With a cheap fee and a few thousand payments the sequential stream often wins. Keep `parallel()` only where the numbers say so, and remember that the pod's CPU limit sets the common pool's size."}
  ]
 },
 "lab": {
  "title": "Fork a ledger, then fix two parallel streams",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/LedgerFees.java", f"{lab}/main/{P}/ParallelPitfalls.java", f"{lab}/main/{P}/FeeModel.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l08.*'",
  "steps": [
   "Run the tests. All six fail.",
   "Write `LedgerFees.compute`. If `to - from <= threshold`, loop over the range and add up `fees.feeCents(amounts[i])`. Otherwise split at the midpoint into two new `LedgerFees` (use the private constructor), fork one half, compute the other, then join.",
   "Fix `ParallelPitfalls.flaggedIds`: keep `parallelStream()`, drop the shared list, and let the stream collect the ids with `map(Payment::id).toList()`.",
   "Fix `ParallelPitfalls.issuers`: start one `supplyAsync(() -> lookup.issuer(bin), io)` per BIN, collect the futures, then join them into the result map on the calling thread.",
   "Run the tests until all six pass, then run them twice more."
  ],
  "hints": [
   "`runsHalvesInParallel` makes the first fee on each thread wait until a second thread arrives. If it times out, your two halves ran one after the other: compute the second half before you join the first.",
   "`(from + to) >>> 1` is a midpoint that can't overflow.",
   "In `issuers`, create every future before you join any of them. A single stream that maps to `supplyAsync` and then to `join` handles one element at a time, so each lookup finishes before the next one starts, and `issuersRunsAllAtOnce` times out."
  ],
  "done_when": "All six tests in `ForkJoinTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A RecursiveTask from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a `RecursiveTask<Long>` that finds the largest amount in a `long[]`, with a threshold of 10,000, and the line that runs it on the common pool. Then compare. Is your `compute()` between the `fork()` and the `join()`?",
  "answer": {"lang": "java", "title": "MaxAmount.java", "src": "class MaxAmount extends RecursiveTask<Long> {\n    final long[] a; final int from, to;\n\n    MaxAmount(long[] a, int from, int to) { this.a = a; this.from = from; this.to = to; }\n\n    @Override\n    protected Long compute() {\n        if (to - from <= 10_000) {\n            long max = Long.MIN_VALUE;\n            for (int i = from; i < to; i++) max = Math.max(max, a[i]);\n            return max;\n        }\n        int mid = (from + to) >>> 1;\n        MaxAmount left = new MaxAmount(a, from, mid);\n        MaxAmount right = new MaxAmount(a, mid, to);\n        left.fork();\n        long r = right.compute();\n        return Math.max(left.join(), r);\n    }\n}\n\nlong max = ForkJoinPool.commonPool().invoke(new MaxAmount(amounts, 0, amounts.length));",
   "alt": {"lang": "kotlin", "title": "MaxAmount.kt", "src": "class MaxAmount(val a: LongArray, val from: Int, val to: Int) : RecursiveTask<Long>() {\n    override fun compute(): Long {\n        if (to - from <= 10_000) {\n            var max = Long.MIN_VALUE\n            for (i in from until to) max = maxOf(max, a[i])\n            return max\n        }\n        val mid = (from + to) ushr 1\n        val left = MaxAmount(a, from, mid)\n        val right = MaxAmount(a, mid, to)\n        left.fork()\n        val r = right.compute()\n        return maxOf(left.join(), r)\n    }\n}\n\nval max = ForkJoinPool.commonPool().invoke(MaxAmount(amounts, 0, amounts.size))"}}
 },
 "recap": [
  "A `RecursiveTask` splits its range until it is below a threshold, then loops. The `ForkJoinTask` Javadoc suggests roughly 100 to 10,000 basic steps per leaf.",
  "Fork one half, compute the other on this thread, then join. Joining before computing runs every split one half after the other.",
  "Each worker pushes and pops at the top of its own deque; idle workers steal the oldest, biggest task from the bottom of someone else's. `join()` helps instead of just waiting.",
  "Parallel streams run on `ForkJoinPool.commonPool()` plus the calling thread: cores minus one workers, shared with every default-executor `CompletableFuture` in the JVM.",
  "Never write to shared state from a parallel stream. Let `toList()`, `collect`, `sum` or `reduce` build the result.",
  "Blocking calls starve the common pool. Run I/O on an executor built for waiting; `ManagedBlocker` is a patch for code you can't move."
 ],
 "quiz": [
  {
   "q": "Which `compute()` body lets the two halves run at the same time?",
   "options": [
    "`left.fork(); long l = left.join(); return l + right.compute();`",
    "`return left.compute() + right.compute();`",
    "`left.fork(); long r = right.compute(); return left.join() + r;`",
    "`long r = right.compute(); left.fork(); return left.join() + r;`"
   ],
   "answer": 2,
   "why": "Only the third one makes the left half stealable and then keeps this thread busy with the right half while a thief can run the left. The first and last both wait for one half before the other is available, and the second never forks at all. All four give the right answer, which is why the bug is easy to miss."
  },
  {
   "q": "An 8-core pod runs `cardIds.parallelStream().map(issuer::lookup).toList()`, and each lookup takes 120 ms. What is the biggest risk?",
   "options": [
    "None: parallel streams run on virtual threads",
    "The lookups occupy the common pool's 7 workers, so other parallel streams and executor-less `CompletableFuture` tasks in the JVM wait behind them",
    "The stream silently falls back to running sequentially because the calls block",
    "It throws, because blocking isn't allowed in a `ForkJoinPool`"
   ],
   "answer": 1,
   "why": "Parallel streams use the common pool's platform workers, which the whole JVM shares, and the pool can't tell that a worker is blocked. Nothing throws and nothing falls back: everything else that needs the common pool just waits. Run the lookups on an IO executor instead."
  },
  {
   "q": "`List<String> ids = new ArrayList<>(); payments.parallelStream().forEach(p -> ids.add(p.id()));` runs over 100,000 payments. What do you get, most of the time?",
   "options": [
    "Fewer than 100,000 ids, or an `ArrayIndexOutOfBoundsException`",
    "All 100,000 ids, in the original order",
    "All 100,000 ids, in a scrambled order",
    "A `ConcurrentModificationException`, every time"
   ],
   "answer": 0,
   "why": "Several threads call `add` on one `ArrayList`, which isn't thread-safe: writes race on the size and the backing array, so ids get lost or the array index runs past the end. `ConcurrentModificationException` comes from iterating while modifying, not from this race. `payments.parallelStream().map(Payment::id).toList()` is correct and keeps the order."
  },
  {
   "q": "Pick the tool for each job: (1) total the fees over 20 million ledger rows already in memory; (2) make 300 calls to a card-issuer API.",
   "options": [
    "(1) virtual threads; (2) a parallel stream",
    "Both in one parallel stream",
    "(1) a single-thread executor; (2) `supplyAsync` without an executor",
    "(1) a parallel stream or a `RecursiveTask`; (2) an IO executor or virtual threads, combined with `CompletableFuture`"
   ],
   "answer": 3,
   "why": "In-memory CPU work splits well and wants about one thread per core, which is what the common pool gives you. Waiting on an API wants many threads that are cheap to block, and they must not be the common pool's. `supplyAsync` without an executor would put those calls right back on the common pool."
  },
  {
   "q": "From \"CompletableFuture: composing async steps\": one part of a service calls `supplyAsync(task)` with no executor, another uses `parallelStream()`. Do they compete for threads?",
   "options": [
    "No: `CompletableFuture` has its own default pool",
    "Yes: both use `ForkJoinPool.commonPool()` (on JDK 25 always, on JDK 21 whenever its parallelism is at least 2)",
    "Only when both run on virtual threads",
    "No: every parallel stream creates its own pool"
   ],
   "answer": 1,
   "why": "The default async executor is the common pool, and so is the pool behind parallel streams. Before JDK 25 the one exception was a common pool with parallelism below 2, where `CompletableFuture` used a thread per task instead. Either way, a blocking task in one slows down the other.",
   "from": "exec-06"
  }
 ],
 "flashcards": [
  {"front": "In `compute()`, what is the right order of fork, compute and join?", "back": "Fork one half, compute the other half on this thread, then join the forked half. Joining first runs the halves one after the other."},
  {"front": "Where does a ForkJoinPool worker take its own tasks from, and where does a thief steal from?", "back": "The owner pushes and pops at the top of its deque (newest first). A thief takes from the bottom (oldest, biggest task)."},
  {"front": "Default parallelism of `ForkJoinPool.commonPool()`?", "back": "`availableProcessors() - 1` (at least 1). Change it with `-Djava.util.concurrent.ForkJoinPool.common.parallelism`."},
  {"front": "Which threads run a parallel stream?", "back": "Common pool workers plus the thread that started the stream."},
  {"front": "Why is a blocking call inside a parallel stream a problem for the whole JVM?", "back": "It holds a common pool worker, and that pool is shared by every parallel stream and every executor-less CompletableFuture."},
  {"front": "What does `ForkJoinPool.managedBlock` do?", "back": "Tells the pool that a worker is about to block, so the pool can start a spare thread to keep its parallelism up."},
  {"front": "How big should a fork/join leaf be, by the ForkJoinTask Javadoc's rough rule?", "back": "More than about 100 and fewer than about 10,000 basic computational steps. Then measure."}
 ],
 "terms": [
  {"term": "ForkJoinPool", "plain": "A pool where each worker has its own deque and idle workers steal tasks from busy ones."},
  {"term": "RecursiveTask", "plain": "A fork/join task that returns a value; RecursiveAction returns nothing."},
  {"term": "Work stealing", "plain": "An idle worker takes a task from the far end of another worker's deque."},
  {"term": "Deque", "plain": "A double-ended queue: the owner uses one end, thieves the other."},
  {"term": "Threshold", "plain": "The size below which a task stops splitting and just loops."},
  {"term": "Common pool", "plain": "The JVM-wide ForkJoinPool behind parallel streams and default async tasks."},
  {"term": "ManagedBlocker", "plain": "A way to tell a ForkJoinPool a worker will block, so it can add a spare thread."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate how work stealing keeps four workers busy on a recursive ledger sum, and why `left.fork(); left.join(); right.compute()` gets no speed-up even though it forks.",
  "answer": "Each worker has its own deque. When a task splits, it forks one half onto the top of its worker's deque and works on the other half itself. Idle workers steal from the bottom of a busy worker's deque, where the oldest and largest piece sits, split it on their own deques, and so the work spreads across all four with only a few steals. `join` either runs the task itself, if nobody stole it, or helps with other work while it waits. With `fork` immediately followed by `join`, the worker waits for the left half before it starts the right half. Even if a thief takes the left half, the forking worker just waits for it, so the two halves of every split never overlap and the total time is about the same as one thread."
 },
 "deeper": {
  "minutes": 8,
  "body": "The virtual thread scheduler that the next track covers is also a `ForkJoinPool`, a separate instance from the common pool. JEP 444 describes it as a work-stealing `ForkJoinPool` that operates in FIFO mode. FIFO mode exists for tasks that are submitted and never joined, like events or messages: you get it with the `asyncMode` argument of the four-argument `ForkJoinPool` constructor, and each worker then takes its own tasks oldest first instead of newest first.\n\nThe common pool has a few more knobs, all system properties read once when the pool starts: `java.util.concurrent.ForkJoinPool.common.parallelism`, `.threadFactory`, `.exceptionHandler` and `.maximumSpares`, which caps the spare threads that `managedBlock` can add. Calling `close()` or `shutdown()` on the common pool does nothing, so library code can't switch it off by accident.\n\nWhy does `availableProcessors() - 1` make sense? Because the thread that calls `invoke` or starts a parallel stream works too. Seven workers plus the caller keep eight cores busy. It also means that on a 2-CPU container the common pool has one worker, and before JDK 25 that was enough for `CompletableFuture` to stop using it (lesson 6).\n\nParallel streams don't use `RecursiveTask` internally. They use `CountedCompleter`, a `ForkJoinTask` that counts pending subtasks and runs a completion action when the count reaches zero, so no thread ever waits in `join()`. You rarely need to write one yourself, but it is the reason a parallel stream can split deep trees without stacking up joins."
 },
 "sources": [
  {"title": "ForkJoinPool (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ForkJoinPool.html"},
  {"title": "ForkJoinTask (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ForkJoinTask.html"},
  {"title": "java.util.stream package summary (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "Dispatchers.Default (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-default.html"}
 ]
}
out = ROOT / "content/lessons/exec-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
