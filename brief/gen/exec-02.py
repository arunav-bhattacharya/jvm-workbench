import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l02"
read = lambda p: (ROOT / p).read_text()
KP = "kotlin/workbench/executors/l02"
def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l02.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l02.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

SVG = (
    '<svg viewBox="0 0 640 330" role="img" aria-label="ThreadPoolExecutor decision flow: below core start a thread, else queue, else grow to max, else reject">'
    '<rect class="box" x="20" y="12" width="180" height="36" rx="8"/>'
    '<text class="t t-code" x="110" y="35" text-anchor="middle">execute(task)</text>'
    '<rect class="box-b" x="20" y="72" width="180" height="40" rx="8"/>'
    '<text class="t" x="110" y="97" text-anchor="middle">threads &lt; core?</text>'
    '<rect class="box-b" x="20" y="142" width="180" height="40" rx="8"/>'
    '<text class="t" x="110" y="167" text-anchor="middle">room in queue?</text>'
    '<rect class="box-b" x="20" y="212" width="180" height="40" rx="8"/>'
    '<text class="t" x="110" y="237" text-anchor="middle">threads &lt; max?</text>'
    '<rect class="box-bad" x="20" y="282" width="180" height="36" rx="8"/>'
    '<text class="t" x="110" y="305" text-anchor="middle">reject: handler</text>'
    '<rect class="box-ok" x="330" y="72" width="280" height="40" rx="8"/>'
    '<text class="t" x="470" y="97" text-anchor="middle">start a core thread</text>'
    '<rect class="box" x="330" y="142" width="280" height="40" rx="8"/>'
    '<text class="t" x="470" y="167" text-anchor="middle">wait in the queue</text>'
    '<text class="t-s t-m" x="470" y="201" text-anchor="middle">only a full queue lets the pool grow</text>'
    '<rect class="box-a" x="330" y="212" width="280" height="40" rx="8"/>'
    '<text class="t" x="470" y="237" text-anchor="middle">start an extra thread</text>'
    '<line class="ln" x1="110" y1="48" x2="110" y2="70" marker-end="url(#arr)"/>'
    '<line class="ln" x1="110" y1="112" x2="110" y2="140" marker-end="url(#arr)"/>'
    '<line class="ln" x1="110" y1="182" x2="110" y2="210" marker-end="url(#arr)"/>'
    '<line class="ln" x1="110" y1="252" x2="110" y2="280" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="128" y="131" text-anchor="middle">no</text>'
    '<text class="t-s t-m" x="128" y="201" text-anchor="middle">no</text>'
    '<text class="t-s t-m" x="128" y="271" text-anchor="middle">no</text>'
    '<line class="ln-a" x1="200" y1="92" x2="326" y2="92" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="162" x2="326" y2="162" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="232" x2="326" y2="232" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="263" y="84" text-anchor="middle">yes</text>'
    '<text class="t-s t-a" x="263" y="154" text-anchor="middle">yes</text>'
    '<text class="t-s t-a" x="263" y="224" text-anchor="middle">yes</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Last lesson, one line gave us a kitchen: `Executors.newFixedThreadPool(4)`. That's four threads taking tasks from one queue, like four cooks taking tickets from a rail. (A thread is one path of work running beside others in the same program.) Most Java code starts its pools this way, for good reasons. The line is short, it works, and on a quiet day it never causes trouble.

Trouble comes on a busy evening. Say orders arrive faster than four cooks can cook them. The rail grows by a few tickets every second, and nothing complains. Someone notices that the kitchen is slow and rebuilds the pool with a maximum of 64 threads, keeping the same rail. The setting is there, the code compiles, and not one extra cook turns up.

That surprises almost everyone. The reason is four short rules inside `ThreadPoolExecutor`, the class behind that one line. In this lesson, we'll follow seven orders through those rules and see why the maximum can be dead code. Then we'll decide what happens to an order nobody can take, and watch the extra cooks go home. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_CTOR = """new ThreadPoolExecutor(
    2,                                      // corePoolSize: the permanent cooks
    4,                                      // maximumPoolSize: permanent plus temporary
    60, TimeUnit.SECONDS,                   // keepAliveTime: how long an idle temp stays
    new ArrayBlockingQueue<>(2),            // the work queue: a rail with room for 2
    new ThreadPoolExecutor.AbortPolicy());  // the door policy when everything is full"""
K_CTOR = """ThreadPoolExecutor(
    2,                                      // corePoolSize: the permanent cooks
    4,                                      // maximumPoolSize: permanent plus temporary
    60, TimeUnit.SECONDS,                   // keepAliveTime: how long an idle temp stays
    ArrayBlockingQueue(2),                  // the work queue: a rail with room for 2
    ThreadPoolExecutor.AbortPolicy())       // the door policy when everything is full"""

S0 = """Before any code, here are one kitchen's rules in plain words. The kitchen has two permanent cooks. Its rail has room for two tickets. When the rail is full, the manager may phone for temporary cooks, up to two of them. And when every cook is busy and the rail is full, a door policy decides what happens to the next customer.

`ThreadPoolExecutor` has a setting for each part of that picture, and its main constructor takes them in this order:

""" + pair(J_CTOR, K_CTOR) + """

The **core pool size** is the number of threads the pool keeps, even when they're idle: the permanent cooks. The **maximum pool size** is the most threads it may ever run, permanent and temporary together. The **keep-alive time** is how long a temporary thread may sit idle before it's sent home.

The **work queue** is the rail, a line where tasks join at the back and leave from the front. Here it's an `ArrayBlockingQueue` with room for two. The **rejection handler** is the door policy, and `AbortPolicy`, the default, simply refuses.

Every call to `execute` walks the same four rules, in this order:

1. Fewer threads than the core size? Start a new thread for this task, even if other threads are idle.
2. Otherwise, offer the task to the queue.
3. The queue said no? Start a new thread, if that stays within the maximum.
4. Still no room? Hand the task to the rejection handler.

Read rule 3 again, because it surprises almost everyone. The pool grows past its core size only when the queue is full. Most people expect the opposite: use more threads first, and queue when you run out.

But the manager is thrifty. A ticket on the rail costs nothing, and a temporary cook costs wages, so temps are called only when the rail has no room left. In code, extra threads are a relief valve for bursts, not the pool's main capacity.

Let's run it. Seven orders arrive at once, and each one takes 500 ms to cook. Write down where you think each order goes, then compare with what `PoolPuzzleDemo` printed. (It calls each order a task, a piece of work handed to the pool.)

```text
core=2 max=4 queue=bounded policy=abort
task 1 accepted: threads=1 queued=0
task 2 accepted: threads=2 queued=0
task 3 accepted: threads=2 queued=1
task 4 accepted: threads=2 queued=2
task 5 accepted: threads=3 queued=2
task 6 accepted: threads=4 queued=2
task 7 REJECTED: threads=4 queued=2
```

Tasks 1 and 2 started the two core threads (rule 1). Tasks 3 and 4 waited on the rail (rule 2). Tasks 5 and 6 found the rail full and got temporary threads (rule 3). Task 7 found everything full, and the door policy turned it away with a `RejectedExecutionException` (rule 4).

Now look at who finished first:

```text
    task 1 done on pool-1-thread-1
    task 6 done on pool-1-thread-4
    task 2 done on pool-1-thread-2
    task 5 done on pool-1-thread-3
    task 3 done on pool-1-thread-1
    task 4 done on pool-1-thread-4
all done in 1050 ms, completed tasks: 6
```

Tasks 5 and 6 were cooked before tasks 3 and 4, although they arrived later. A new thread takes the task that made the manager call it, not the oldest ticket on the rail.

Here the restaurant picture breaks: a real kitchen would cook the oldest ticket first. So even a pool whose queue is first in, first out doesn't promise to run tasks in the order they arrived.

**The pool queues first and grows second. Only a full queue brings in extra threads.**

That rule has a sharp edge. If the queue can never fill, rule 3 never runs at all."""

# ---------------------------------------------------------------- section 1
J_FIXED = """// what Executors.newFixedThreadPool(n) builds
new ThreadPoolExecutor(n, n, 0, TimeUnit.MILLISECONDS, new LinkedBlockingQueue<>());"""
K_FIXED = """// what Executors.newFixedThreadPool(n) builds
ThreadPoolExecutor(n, n, 0, TimeUnit.MILLISECONDS, LinkedBlockingQueue())"""

S1 = """`Executors.newFixedThreadPool(n)`, the line from last lesson, is a `ThreadPoolExecutor` with these settings:

""" + pair(J_FIXED, K_FIXED) + """

The queue is a `LinkedBlockingQueue` with no capacity given, which means it has no limit: a rail with no end. So rule 2 always succeeds. Rule 3 never runs, so no extra thread is ever started, and rule 4 never runs either, so nothing is ever rejected.

Let's put that queue into our seven-order kitchen and keep the maximum of four. Run the demo with `unbounded`, and the end of the output reads:

```text
task 5 accepted: threads=2 queued=3
task 6 accepted: threads=2 queued=4
task 7 accepted: threads=2 queued=5
...
all done in 2019 ms, completed tasks: 7
```

Every task was accepted, the pool stayed at two threads, and five tasks waited on the rail. All seven finished after about 2,000 ms: four rounds of 500 ms on two cooks. The maximum of four never came into play.

That looks safe. It isn't, because an endless rail hides overload instead of reporting it. Say orders arrive at 400 a second, and the pool can finish 300. The rail grows by 100 tasks every second.

After ten minutes, 60,000 tasks are waiting, each one holding its order in memory. A new order now waits more than three minutes before a thread even looks at it. The customer gave up long ago, so the kitchen is busy cooking dinners nobody will eat. The first alarm is usually the heap, the memory where Java keeps its objects, running out.

Raising the maximum on such a pool changes nothing. `new ThreadPoolExecutor(10, 100, 60, SECONDS, new LinkedBlockingQueue<>())` runs 10 threads, forever. The `100` is dead code: it compiles, and it never does anything.

`newCachedThreadPool()` fails the other way. It's `new ThreadPoolExecutor(0, Integer.MAX_VALUE, 60, SECONDS, new SynchronousQueue<>())`, and a `SynchronousQueue` has no room at all. A task gets in only if an idle thread is waiting to take it right then, like a plate passed straight into a free cook's hands. That's called a **direct handoff**.

Under a burst no thread is idle, so every task gets a new thread. Two thousand slow tasks means two thousand threads, which is the manager's hiring habit from last lesson. Run the demo with `handoff` to see it with our maximum of four. Tasks 1 to 4 each get a thread, nothing ever queues, and tasks 5, 6 and 7 are rejected.

There's one shape that pushes back: a **bounded queue with a finite maximum**. Then rule 4 can fire, and overload turns into a visible event that you choose how to handle. Lesson 3 of this track picks the sizes. This lesson picks the shape.

**An unbounded queue never says no, so the pool never grows and never rejects. Give the queue a limit.**

One odd case is worth knowing. With a core size of 0 and an unbounded queue, rule 1 never starts a thread and rule 3 never runs. It looks as if nothing would ever run. The pool handles this as a special case: after it queues a task, if it has no threads at all, it starts one. You get a pool with a single thread.

With a limit on the queue, rule 4 can finally fire. The question is what rule 4 should do."""

# ---------------------------------------------------------------- section 2
S2 = """When rule 4 fires, the pool calls its `RejectedExecutionHandler`, the door policy. The same handler also runs for any task submitted after `shutdown()`. The JDK, Java's standard library and tools, ships four policies, and each one makes someone different pay:

| Policy | What happens to the task | Who notices |
|---|---|---|
| `AbortPolicy` (the default) | `execute` throws `RejectedExecutionException` | the caller, at once |
| `CallerRunsPolicy` | the thread that called `execute` runs the task itself | the caller, by being slowed down |
| `DiscardPolicy` | dropped | nobody |
| `DiscardOldestPolicy` | the oldest queued task is dropped, then the new one is tried again | nobody |

In the kitchen, `AbortPolicy` tells the customer at the door, plainly, that the kitchen is full. `CallerRunsPolicy` sends the waiter who brought the order into the kitchen to cook it himself, and while he cooks, he takes no new orders. `DiscardPolicy` drops the ticket in the bin. `DiscardOldestPolicy` bins the oldest ticket on the rail to make room for the new one.

`AbortPolicy` is the right default when a person or a program is waiting for an answer. The caller gets an exception that it can turn into a polite "try again later", and you can count the rejections.

`CallerRunsPolicy` is **back-pressure** in one line: a full pool pushing back on whoever feeds it. While the submitting thread is busy running a task, it isn't submitting more, so the producer, the thread that feeds the pool, slows down to the pool's speed. Run the demo with `"bounded caller"` and watch task 7:

```text
task 6 accepted: threads=4 queued=2
    task 1 done on pool-1-thread-1
    task 2 done on pool-1-thread-2
    task 5 done on pool-1-thread-3
    task 6 done on pool-1-thread-4
    task 7 done on main
task 7 accepted: threads=4 queued=0
```

Task 7 ran on `main`, the thread that called `execute`. So the line `task 7 accepted` printed only after `task 7 done on main`, 500 ms later, and `main` handed the pool nothing new in the meantime.

That suits a job that reads a file and hands out the work. It's a bad idea when the submitting thread has a job of its own that can't wait, such as a thread that reads incoming requests for everyone. Making it cook stalls everyone it serves. And after `shutdown()`, `CallerRunsPolicy` drops tasks silently.

The two discard policies lose work without a trace, and they have a nastier side with `submit`. A dropped task never runs, so its `Future`, the claim ticket that `submit` returns, never completes. A caller waiting in `get()` waits forever, like a customer still sitting at the table for a dish that went in the bin. Use them only for work that is truly optional, such as a statistic you can afford to miss.

**When the pool is full, someone pays. Choose who, on purpose.**

In real code you usually want a handler of your own. It counts the rejection for a dashboard, then fails fast with a message that says how full the pool was. The interface has one method, `rejectedExecution(Runnable task, ThreadPoolExecutor pool)`, and the lab has you write one.

We know now where a task goes when it arrives. What happens to the extra cooks once the rush is over is the last piece."""

ASIDE2 = {
    "title": "What does a rejection look like from outside?",
    "body": "If you write web services, programs that answer requests over the network, a rejected task usually becomes a quick reply that says \"busy, try again later\". On the web, that reply has a standard number, status 503, Service Unavailable. It's kinder than a request that waits three minutes in an endless queue and then times out, because the caller learns at once and can retry later or try another copy of the service. Count your rejections and put the count on a dashboard. A rising count is the earliest warning that you've run out of capacity."
}

# ---------------------------------------------------------------- section 3
S3 = """Threads above the core size are temporary. If one sits idle for longer than the keep-alive time, it exits, and the pool shrinks back toward its core size. Core threads stay, even if they're idle for a week.

`KeepAliveDemo` shows the whole cycle. Its pool has core 2, max 4, a rail of 2 and a keep-alive of 300 ms. It gets six orders of 200 ms each, and then prints the pool every 150 ms:

```text
before any task: threads=0
   0 ms: threads=4 active=4 queued=2
 201 ms: threads=4 active=2 queued=0
 352 ms: threads=4 active=2 queued=0
 507 ms: threads=2 active=0 queued=0
 658 ms: threads=2 active=0 queued=0
 ...
largest pool size seen: 4
```

The pool starts with no threads at all, because even core threads are created lazily, one per task, the first time tasks arrive. The burst pushes it to 4. At about 200 ms, two threads finish their orders and find the rail empty. Three hundred milliseconds later they're sent home, so by 507 ms the pool is back to two threads, its core size.

Two methods change that default. `allowCoreThreadTimeOut(true)` applies the keep-alive to core threads too, so an idle pool can shrink to zero. That suits a pool used for a report once a night, which then holds no threads for the rest of the day. It needs a keep-alive above zero, or the call throws an `IllegalArgumentException`. Run the demo with `core`, and the pool goes from 4 threads to 2, then to 0.

`prestartAllCoreThreads()` goes the other way. It starts all the core threads up front, the way cooks arrive before the doors open. Then the first rush after the program starts doesn't also wait for threads to be created. The Javadoc, the JDK's official documentation of its classes, also recommends it when you build a pool around a queue that already holds tasks. A pool with no threads would never look at them.

You can watch the pool through its getters: `getPoolSize()` (threads alive now), `getActiveCount()` (threads running a task), `getLargestPoolSize()` (the highest it has been) and `getQueue().size()`. They're approximate while the pool is busy, which is fine for a dashboard. Lesson 9 of this track turns them into measurements.

For most pools that answer requests, I'd set the core size equal to the maximum, and rely on a bounded queue and a rejection policy. A pool that changes size under load is harder to reason about, and its extra threads arrive exactly when the machine is busiest. I'd keep core below max only when bursts are short and rare, and absorbing them beats turning work away.

That's the whole machine: four rules, a queue, a door policy and a clock for idle threads. Every one of those settings is a number, though, and this lesson never said how to choose one."""

L = {
 "id": "exec-02",
 "title": "Inside ThreadPoolExecutor: core, max, queue, rejection",
 "minutes": 35,
 "goal": "By the end you can predict where every task in a burst goes (a core thread, the queue, an extra thread, or the rejection handler) and configure a ThreadPoolExecutor that pushes back instead of growing without limit.",
 "opening": OPENING,
 "warmup": {
  "q": "`new ThreadPoolExecutor(2, 10, 60, SECONDS, new LinkedBlockingQueue<>())` gets a burst of 50 tasks that each take 2 seconds. What is the most threads it will run at once?",
  "options": [
   "10, the maximum pool size",
   "50, one per task",
   "2, the core pool size",
   "12, core plus max"
  ],
  "answer": 2,
  "why": "The pool adds threads beyond its core size only when the queue refuses a task. A `LinkedBlockingQueue` with no capacity never refuses, so the pool stays at 2 threads and 48 tasks wait in the queue. The maximum of 10 never comes into play. The second section shows it happening."
 },
 "sections": [
  {
   "h": "Seven orders through four rules: where every task goes",
   "body": S0,
   "figure": {"svg": SVG, "caption": "Every execute() call walks these four checks in order. The pool only grows toward max after the queue refuses a task."},
   "try": {
    "title": "Predict a burst, then run it",
    "minutes": 4,
    "steps": [
     "Without running anything, write down where tasks 1 to 7 go for `new ThreadPoolExecutor(2, 4, 60, SECONDS, new ArrayBlockingQueue<>(2))`.",
     "Run `PoolPuzzleDemo` (the Java and Kotlin versions print the same) with the command below, and compare with your notes.",
     "Look at the `done on` lines. Which tasks finished first, and on which threads?"
    ],
    "code": demo("PoolPuzzleDemo"),
    "expect": "The same as the output in this section: two core threads, two queued, two extra threads, one rejection. Tasks 1, 2, 5 and 6 finish first, at about 500 ms, in whatever order their threads wake up. Then tasks 3 and 4 run on two of those threads and finish at about 1,000 ms. Task 7 never runs."
   }
  },
  {
   "h": "A rail with no end: how an unbounded queue makes the maximum dead code",
   "body": S1,
   "try": {
    "title": "Swap the queue",
    "minutes": 3,
    "steps": [
     "Predict the thread count and the total time for the same seven tasks with an unbounded queue. Then run the demo with `-Pargs=unbounded`.",
     "Do the same with `-Pargs=handoff`, which uses a `SynchronousQueue`."
    ],
    "expect": "With `unbounded`, the pool never goes past 2 threads, all seven tasks are accepted, five of them queue, and the run takes about 2,000 ms (four rounds of 500 ms). With `handoff`, nothing ever queues: tasks 1 to 4 each get a thread, and tasks 5, 6 and 7 are rejected, because the maximum is 4 and a `SynchronousQueue` holds nothing."
   },
   "refs": [
    {"title": "ThreadPoolExecutor (Java SE 25 API), section Queuing", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html", "kind": "docs"}
   ]
  },
  {
   "h": "When everything is full: four rejection policies, and who pays",
   "body": S2,
   "aside": ASIDE2,
   "try": {
    "title": "Try the other three policies",
    "minutes": 4,
    "steps": [
     "Run the demo with `-Pargs=\"bounded caller\"`. Find the line for task 7. Which thread ran it, and when was its `accepted` line printed?",
     "Run it with `-Pargs=\"bounded discard\"` and then `-Pargs=\"bounded oldest\"`. Count the `done` lines, and work out which task disappeared each time."
    ],
    "expect": "With `caller`, task 7 runs on `main`, so `main` is stuck for 500 ms and prints \"task 7 accepted\" only after `task 7 done on main`. The pool reports 6 completed tasks, because task 7 never ran on it. With `discard`, task 7 is \"accepted\" and simply never runs: six `done` lines, and no error. With `oldest`, task 3, the oldest task in the queue, vanishes and task 7 runs in its place. Neither discard policy says a word about it."
   }
  },
  {
   "h": "After the rush: keep-alive, core time-out and starting threads early",
   "body": S3,
   "try": {
    "title": "Watch the pool shrink",
    "minutes": 3,
    "steps": [
     "`KeepAliveDemo` runs a pool with core 2, max 4, a queue of 2 and a 300 ms keep-alive. It submits six 200 ms tasks, then prints the pool every 150 ms. Predict the thread count at the end, then run it.",
     "Run it again with `-Pargs=core`, which also calls `allowCoreThreadTimeOut(true)`."
    ],
    "code": demo("KeepAliveDemo"),
    "expect": "The pool starts with 0 threads, jumps to 4 during the burst, and drops back to 2 a few hundred milliseconds after the work ends. The largest pool size reported is 4. With `core`, it drops from 4 to 2 and then to 0, because the core threads now retire too."
   }
  }
 ],
 "compare": {
  "title": "Configuring the same pool from Java and Kotlin",
  "java": {"title": "AuthPool.java (solution)", "src": read(f"{lab}/solution/{P}/AuthPool.java")},
  "kotlin": {"title": "AuthPoolConfig.kt", "src": read(f"{lab}/demo/kotlin/workbench/executors/l02/AuthPoolConfig.kt")},
  "note": "Both build the lab's pool: 4 core threads, at most 8, a queue of 16, a 30-second keep-alive, and core threads started early. The Kotlin version also swaps the default policy for a lambda that counts each rejection and then throws. Two things differ when you build the pool from Kotlin. Kotlin doesn't allow named arguments when it calls a Java constructor, so the positional numbers need comments in both languages. And Kotlin turns a lambda into a Java interface with one method, so the `RejectedExecutionHandler` can be a trailing lambda instead of a class. The getters read as properties (`pool.queue`, `pool.poolSize`). In code that uses coroutines, Kotlin's own light tasks, you rarely build a pool at all: `Dispatchers.IO` is already a shared pool capped at 64 threads (or the number of cores, if that's larger), and `limitedParallelism(n)` gives you a smaller limit on top of it."
 },
 "worked": {
  "title": "Trace a burst through the checkout's card pool",
  "steps": [
   {"say": "This is the pool from the lab, `AuthPool`. A shop's checkout uses it for card authorizations: each task asks the customer's bank whether a card payment may go through, and waits about 200 ms for the answer. The pool starts its 4 core threads early, so they're already waiting for work. Then a coach party pays at the same moment, and 30 tasks arrive together. Before reading on, write down how many threads start, how many tasks queue and how many are rejected.",
    "code": "ThreadPoolExecutor pool = new ThreadPoolExecutor(\n        4, 8, 30, TimeUnit.SECONDS,\n        new ArrayBlockingQueue<>(16),\n        new ThreadPoolExecutor.AbortPolicy());\npool.prestartAllCoreThreads();", "lang": "java",
    "alt_code": "val pool = ThreadPoolExecutor(\n    4, 8, 30, TimeUnit.SECONDS,\n    ArrayBlockingQueue(16),\n    ThreadPoolExecutor.AbortPolicy())\npool.prestartAllCoreThreads()", "alt_lang": "kotlin"},
   {"say": "Apply the rules in order, and say each core thread grabs its task at once. The four core threads already exist, so tasks 1 to 4 pass through the queue straight into their hands. Tasks 5 to 20 fill the queue of 16 (rule 2). Tasks 21 to 24 find the queue full and start extra threads, up to 8 (rule 3). Tasks 25 to 30 find everything full and are rejected (rule 4).",
    "code": "threads = 8, queued = 16, rejected = 6", "lang": "text"},
   {"say": "Six `RejectedExecutionException`s reach the checkout, and six customers are asked to pay again. Decide on purpose instead. Here, a short pause at the checkout beats six failed payments, so let the thread that submits the payments run the overflow itself.",
    "code": "ThreadPoolExecutor pool = new ThreadPoolExecutor(\n        4, 8, 30, TimeUnit.SECONDS,\n        new ArrayBlockingQueue<>(16),\n        new ThreadPoolExecutor.CallerRunsPolicy());   // the submitting thread runs the overflow", "lang": "java",
    "alt_code": "val pool = ThreadPoolExecutor(\n    4, 8, 30, TimeUnit.SECONDS,\n    ArrayBlockingQueue(16),\n    ThreadPoolExecutor.CallerRunsPolicy())   // the submitting thread runs the overflow", "alt_lang": "kotlin"},
   {"say": "Now tasks 25 to 30 run on the submitting thread, one after another: about 6 x 200 ms = 1.2 s during which it hands the pool nothing new. For a checkout, that's a short pause, and nobody's payment fails. If that thread also had to answer other customers within a deadline, the pause would be the wrong trade. Then you'd keep `AbortPolicy` and ask the customer to try again.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Predict a pool, configure a pool, handle its rejections",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/PoolMath.java", f"{lab}/main/{P}/AuthPool.java", f"{lab}/main/{P}/CountingRejectionHandler.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l02.*'",
  "steps": [
   "Run the tests. All twelve fail.",
   "Write `PoolMath.predict`. Loop over the tasks and apply the four rules to three counters. The tests compare your answers with a real `ThreadPoolExecutor` on eight configurations, including a `SynchronousQueue` (capacity 0) and an unbounded queue.",
   "Write `AuthPool.create` to the spec in its Javadoc. It's the pool a shop's checkout uses to ask the bank about card payments. Don't forget the part about starting the core threads up front.",
   "Write `CountingRejectionHandler`: count every call, return quietly if the pool is shut down, otherwise throw `RejectedExecutionException` with the message format from the Javadoc.",
   "Run the tests until all twelve pass."
  ],
  "hints": [
   "`predict` needs no special case for capacity 0 or `Integer.MAX_VALUE`. The comparison `queued < queueCapacity` already handles both.",
   "`ThreadPoolExecutor` has a constructor that takes a `RejectedExecutionHandler` as its sixth argument. `prestartAllCoreThreads()` is a method you call after construction.",
   "Use a `LongAdder` or an `AtomicLong` for the count: several submitting threads can be rejected at the same moment."
  ],
  "done_when": "All twelve tests in `ThreadPoolExecutorRulesTest` pass."
 },
 "drill": {
  "title": "Run the four rules in your head",
  "minutes": 4,
  "prompt": "Close this page. From memory, write the four rules `ThreadPoolExecutor.execute` applies, in order. Then predict threads, queued and rejected for `new ThreadPoolExecutor(3, 6, 60, SECONDS, new ArrayBlockingQueue<>(4))` with 15 tasks that all block. Last, do the same with `new LinkedBlockingQueue<>()` as the queue.",
  "answer": {"lang": "text", "src": "1. fewer than core threads  -> start a new thread\n2. otherwise                 -> offer to the queue\n3. queue refused             -> start a thread if below max\n4. otherwise                 -> RejectedExecutionHandler\n\nArrayBlockingQueue(4), 15 tasks:\n  tasks 1-3   core threads      threads = 3\n  tasks 4-7   queued            queued  = 4\n  tasks 8-10  extra threads     threads = 6\n  tasks 11-15 rejected          rejected = 5\n\nLinkedBlockingQueue (unbounded), 15 tasks:\n  threads = 3, queued = 12, rejected = 0   (max = 6 is never used)"}
 },
 "recap": [
  "`execute` applies four rules in order: below core, start a thread; otherwise queue; if the queue refuses, grow toward max; otherwise reject.",
  "The pool grows past core only when the queue is full, so with an unbounded queue the maximum does nothing.",
  "`newFixedThreadPool` hides overload in an unbounded queue, and `newCachedThreadPool` turns it into unlimited threads. A bounded queue with a finite maximum pushes back.",
  "`AbortPolicy` throws, `CallerRunsPolicy` slows the submitter down, and the two discard policies lose work silently (and leave `submit` futures that never complete).",
  "`keepAliveTime` retires idle threads above core, `allowCoreThreadTimeOut(true)` retires core threads too, and `prestartAllCoreThreads()` starts them early.",
  "The limit: the four rules say where a task goes, but not what sizes to give the pool and its queue. Choosing them takes measurements, which is the next lesson."
 ],
 "closing": "We started with a kitchen whose maximum of 64 cooks never showed up. Seven orders through four rules showed why. The pool queues first and grows only when the rail is full, so an endless rail keeps the extra cooks at home. Then we chose who pays when everything is full, and watched the temporary cooks go home after the rush.\n\nNow search your own code for a `ThreadPoolExecutor` built with `new LinkedBlockingQueue<>()` and a maximum larger than its core size. That maximum never does anything.\n\nNext, we'll choose the numbers themselves. How many cooks does a kitchen need when they chop all day, and how many when they mostly wait for the oven?",
 "quiz": [
  {
   "q": "`new ThreadPoolExecutor(2, 4, 60, SECONDS, new ArrayBlockingQueue<>(10))` receives 8 tasks that each block for a minute. Where are they?",
   "options": [
    "4 running, 4 queued",
    "2 running, 6 queued",
    "4 running, 2 queued, 2 rejected",
    "8 running"
   ],
   "answer": 1,
   "why": "Tasks 1 and 2 start core threads. The other 6 fit in a queue of 10, so the queue never refuses and the pool never grows. The tempting answer, 4 running, assumes the pool uses its maximum before it queues. It's the other way round."
  },
  {
   "q": "A job reads 2 million sales from a file and submits one task per 1,000 sales. You want it to go no faster than the pool can keep up, without losing a batch of sales and without writing a retry loop. Which policy fits?",
   "options": [
    "`AbortPolicy`",
    "`DiscardOldestPolicy`",
    "`CallerRunsPolicy`",
    "`DiscardPolicy`"
   ],
   "answer": 2,
   "why": "`CallerRunsPolicy` makes the reading thread run the overflow batch itself, so it stops reading while it works. That's back-pressure, and nothing is lost. `AbortPolicy` would make you write the retry loop, and both discard policies lose batches without telling anyone."
  },
  {
   "q": "A pool uses `DiscardPolicy`. A thread calls `pool.submit(task).get()` while the pool is full. What happens?",
   "options": [
    "`get()` throws RejectedExecutionException",
    "`get()` returns null",
    "`get()` throws CancellationException",
    "`get()` blocks forever, because the dropped task never runs and its Future never completes"
   ],
   "answer": 3,
   "why": "`DiscardPolicy` drops the `FutureTask` without running or cancelling it. Nothing will ever complete that `Future`, so `get()` without a timeout waits forever. That's why the Javadoc suggests cancelling dropped tasks in a handler of your own."
  },
  {
   "q": "A pool with core 4, max 16 and a bounded queue grew to 16 threads during a rush an hour ago. Things are quiet now. With default settings, how many threads does it have?",
   "options": [
    "4, because idle threads above core retired after keepAliveTime",
    "16, because threads are never removed",
    "0, because idle threads retire",
    "1, the minimum"
   ],
   "answer": 0,
   "why": "Keep-alive applies to threads above the core size, so the pool shrinks back to 4. It goes down to 0 only if you call `allowCoreThreadTimeOut(true)`."
  },
  {
   "q": "From \"Why pools: Executor, ExecutorService and shutdown\": a producer thread keeps calling `execute` on a `ThreadPoolExecutor` with the default handler after another thread has called `shutdown()`. What does the producer see?",
   "options": [
    "The tasks run, because shutdown() lets queued work finish",
    "A RejectedExecutionException from each execute call",
    "Nothing: the tasks are silently dropped",
    "An IllegalStateException"
   ],
   "answer": 1,
   "why": "After `shutdown()`, new tasks go to the rejection handler, and the default `AbortPolicy` throws `RejectedExecutionException`. Only tasks that were already queued still run. With a discard policy or `CallerRunsPolicy`, they would be dropped silently instead.",
   "from": "exec-01"
  }
 ],
 "flashcards": [
  {"front": "In what order does `ThreadPoolExecutor.execute` try its options?", "back": "Start a thread if below core; otherwise queue; if the queue refuses, start a thread if below max; otherwise reject."},
  {"front": "Why does `newFixedThreadPool(8)` never run more than 8 threads, whatever max you set?", "back": "Its `LinkedBlockingQueue` is unbounded, so the queue never refuses a task, and the pool only grows past core when the queue refuses."},
  {"front": "What queue does `newCachedThreadPool()` use, and what is the risk?", "back": "A `SynchronousQueue` (no capacity) with max `Integer.MAX_VALUE`, so every task that finds no idle thread gets a new thread. Threads grow without limit."},
  {"front": "What does `CallerRunsPolicy` do with an overflow task?", "back": "The thread that called `execute` runs it, which slows that producer down. After shutdown, it drops the task."},
  {"front": "A pool with `DiscardPolicy` drops a task sent with `submit`. What happens to `future.get()`?", "back": "It blocks forever. The task never runs, so its Future never completes."},
  {"front": "What does `keepAliveTime` apply to by default?", "back": "Only to threads above `corePoolSize`. Call `allowCoreThreadTimeOut(true)` to let core threads retire too."},
  {"front": "Does a new extra thread pick up the oldest queued task first?", "back": "No. A thread started by rule 3 runs the task that triggered it, so later tasks can overtake queued ones."}
 ],
 "terms": [
  {"term": "corePoolSize", "plain": "The number of threads the pool keeps, even when idle."},
  {"term": "maximumPoolSize", "plain": "The most threads the pool may run, reached only when the queue is full."},
  {"term": "Work queue", "plain": "The BlockingQueue where tasks wait for a free thread."},
  {"term": "Direct handoff", "plain": "A SynchronousQueue: no storage, so a task passes straight to an idle thread or not at all."},
  {"term": "RejectedExecutionHandler", "plain": "The callback that decides what happens to a task the pool cannot take."},
  {"term": "Back-pressure", "plain": "Slowing the producer down when the consumer can't keep up, instead of piling up work."},
  {"term": "Keep-alive time", "plain": "How long an idle thread above core waits before it exits."}
 ],
 "explain_back": {
  "prompt": "A teammate set `maximumPoolSize` to 64 on a pool built with `new LinkedBlockingQueue<>()`, and says the pool \"can grow to 64 threads under load\". Explain why it can't, and what you would change.",
  "answer": "A ThreadPoolExecutor starts threads beyond its core size only when the queue refuses a task. A LinkedBlockingQueue with no capacity never refuses, so every task past the core threads waits in the queue, and the pool never goes above corePoolSize. The 64 is never used. The queue also grows without limit when we fall behind, so we see memory growth and long waits instead of a clear signal that we're overloaded. I would pick a core size from the expected load, give the queue a capacity, set max as the limit for bursts, and choose a rejection policy on purpose: usually AbortPolicy with a counter when someone waits for an answer, or CallerRunsPolicy if the producer should slow down."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why does `ThreadPoolExecutor` queue before it grows? Its Javadoc lists three ways of queuing and is honest about each. A direct handoff (`SynchronousQueue`) \"avoids lockups when handling sets of requests that might have internal dependencies\", because a task never waits in line behind another task that it depends on, but it needs an unbounded maximum. An unbounded queue suits independent tasks and smooths out bursts, but \"admits the possibility of unbounded work queue growth\". A bounded queue \"helps prevent resource exhaustion\" but \"can be more difficult to tune\": a large queue with a small pool keeps CPU use low and can give \"artificially low throughput\", while a small queue needs a larger pool.\n\nThat first point comes back in lesson 9 of this track as pool-induced deadlock: tasks that wait for other tasks in the same bounded pool.\n\nTwo more details for when you read pool code. First, core and max can be changed while the program runs, with `setCorePoolSize` and `setMaximumPoolSize`. That's how some frameworks resize pools from their settings without a restart. Second, `ScheduledThreadPoolExecutor` extends `ThreadPoolExecutor` but uses its own unbounded queue of delayed tasks, so its max setting has no useful effect: it's a fixed pool of `corePoolSize` threads. Lesson 5 of this track covers it."
 },
 "sources": [
  {"title": "ThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html"},
  {"title": "RejectedExecutionHandler (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/RejectedExecutionHandler.html"},
  {"title": "Executors (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Executors.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 8", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/exec-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
