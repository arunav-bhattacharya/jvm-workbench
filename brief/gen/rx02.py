import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l02"
PK = "kotlin/workbench/reactive/l02"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l02."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """At the bakery counter you can order a cake for Saturday. You fill in a form: one chocolate cake, two layers, "Happy birthday" on top. Nothing gets baked while you write. A form is not a cake, however neatly you fill it in. Baking starts when you sign the form and hand it over, and if you never do, the oven never hears about it.

Reactor, the library this track uses from here on, works the same way. A long, careful chain of Reactor calls bakes nothing. It only fills in a form, and the work starts when someone subscribes. That surprises everyone once, and it leads to two easy mistakes: signing the same form twice, and baking the cake while you're still writing the form.

In Why reactive, the oven started the moment it existed, and only the packer's slip slowed it down. In this lesson, we'll meet Reactor's two types, `Flux` and `Mono`, and watch a chain do nothing until someone subscribes. Then we'll bake a cake twice by accident, and find the eager call hiding in `Mono.just`. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_TYPES = """Flux<String> loaves  = Flux.just("rye-1", "rye-2", "rye-3");
Flux<Integer> trays  = Flux.range(1, 3);
Mono<String> cake    = Mono.just("chocolate cake");
Mono<String> nothing = Mono.empty();
Mono<String> failed  = Mono.error(new IllegalStateException("out of flour"));"""
K_TYPES = """val loaves: Flux<String>  = Flux.just("rye-1", "rye-2", "rye-3")
val trays: Flux<Int>      = Flux.range(1, 3)
val cake: Mono<String>    = Mono.just("chocolate cake")
val nothing: Mono<String> = Mono.empty()
val failed: Mono<String>  = Mono.error(IllegalStateException("out of flour"))"""
J_SUB = """loaves.subscribe(
        l -> box(l),                              // onNext
        e -> log.error("the belt stopped", e),    // onError
        () -> log.info("all loaves boxed"));      // onComplete"""
K_SUB = """loaves.subscribe(
    { l -> box(l) },                              // onNext
    { e -> log.error("the belt stopped", e) },    // onError
    { log.info("all loaves boxed") })             // onComplete"""

S0 = """**Reactor** is a library that implements Reactive Streams, the contract from the last lesson, and adds hundreds of **operators**: methods that each add one step to a stream, like stations along the bakery belt. It is the engine under the reactive parts of the Spring Framework, but you need nothing from Spring to use it. Reactor has two publisher types, and the type tells you how many items to expect.

A `Flux<T>` emits zero to many items, then maybe `onComplete` or `onError`. On the bakery line it's an order for a tray: any number of loaves. All three parts are optional, so a `Flux` with no terminal signal is endless, like `Flux.interval(Duration.ofSeconds(1))`, which ticks once a second forever.

A `Mono<T>` emits at most one item and then completes, or emits only an error. It's an order for one cake: you get the cake, or no cake, or a note that says what went wrong. It can never send an item and then an error. `Mono<Void>` means "tell me when it's done", for a job that returns nothing, such as cleaning the oven.

""" + pair(J_TYPES, K_TYPES) + """

Both types implement `org.reactivestreams.Publisher`, so every rule from the last lesson applies. The split is for readers and for operators. A method that returns `Mono<Cake>` promises one cake or none, and `Mono` has operators that only make sense for one value, such as `Mono.zip` from lesson 4 of this track. Some operators change the type: `mono.concatWith(other)` gives a `Flux`, while `mono.then(other)` gives a `Mono`.

The simplest way to run one is `subscribe` with up to three lambdas, one for each kind of signal:

""" + pair(J_SUB, K_SUB) + """

This form writes one slip for everything, `request(Long.MAX_VALUE)`. `FirstFluxDemo`, in the Try it, adds `log()` to the chain, an operator that prints every signal passing through it. The protocol from the last lesson appears line by line:

```text
[ INFO] (main) | onSubscribe([Synchronous Fuseable] FluxArray.ArraySubscription)
[ INFO] (main) | request(unbounded)
[ INFO] (main) | onNext(rye-1)
got rye-1
...
[ INFO] (main) | onComplete()
done
```

The demo's second subscriber leaves out the error lambda, and its `Mono` fails with "out of flour". Reactor doesn't throw that to your code. It prints an `ERROR` log line about `ErrorCallbackNotImplemented`, and `main` carries on, cheerfully unaware. So a test that doesn't check for the error passes. The cause is rule 2.13 from the last lesson: `onError` must return normally, so the subscriber that `subscribe` builds for you can't throw. With no error lambda, it hands the error to a hook, a method Reactor calls for errors nobody handles, and the default hook only logs it.

**A subscribe without an error lambda turns failures into log lines. Always pass one.**

Reactive Streams forbids `null` items, and Reactor 3.8 enforces it: `Mono.just(null)` throws a `NullPointerException`, and so does a `map` whose function returns `null`. Use `Mono.empty()` for "no value". Kotlin catches this even earlier. Reactor 3.8 marks its API with JSpecify annotations, small labels that say whether `null` is allowed, so a Kotlin `map { if (ok) x else null }` doesn't even compile.

Every `subscribe` so far ran its chain at once. Let's slow down and look at what happens before the subscribe."""

# ---------------------------------------------------------------- section 1
J_ASM = """Flux<Integer> pricesInCents = Flux.range(1, 3)
        .map(euros -> euros * 100);              // nothing has run yet
pricesInCents.subscribe(System.out::println);    // now range and map run"""
K_ASM = """val pricesInCents: Flux<Int> = Flux.range(1, 3)
    .map { euros -> euros * 100 }                // nothing has run yet
pricesInCents.subscribe { println(it) }          // now range and map run"""
J_DROP = """Flux<Integer> orderSizes = Flux.just(5, 50, 500);
orderSizes.filter(loaves -> loaves > 10);        // Naive: the new Flux is thrown away
orderSizes.subscribe(loaves -> System.out.println("big order: " + loaves + " loaves"));"""
K_DROP = """val orderSizes: Flux<Int> = Flux.just(5, 50, 500)
orderSizes.filter { loaves -> loaves > 10 }      // Naive: the new Flux is thrown away
orderSizes.subscribe { loaves -> println("big order: $loaves loaves") }"""

S1 = """Here is the most important fact about Reactor: building a chain runs none of your code.

""" + pair(J_ASM, K_ASM) + """

Three separate passes happen over that chain, and it helps to keep them apart. The figure below draws them.

**Assembly** is when you call the operators. Each call returns a new `Flux` that wraps the one before it, so `Flux.range(1, 3).map(...)` is a `FluxMap` object holding a `FluxRange` object. Your lambda is stored, not called. This is filling in the order form. The Reactor docs call the result "an abstract description of your asynchronous process".

**Subscription** is when you call `subscribe`. Reactor walks the chain backwards, from your end to the source. Your subscriber subscribes to `map`, and `map` makes a subscriber of its own and subscribes to `range`. Then `request(n)` travels up the same chain to the source. This is signing the form and handing it over.

**Data** comes last. Only now does the source emit. `onNext` signals flow down through each operator to your lambda, then `onComplete` or `onError`. This is the baking.

`AssemblyDemo`, in the Try it, counts how often `map` runs, before and after `subscribe`:

```text
after assembly: map ran 0 times
price 100 cents
price 200 cents
price 300 cents
after subscribe: map ran 3 times
```

Zero, then three. The form was filled in, and nothing was baked until it was signed.

Three consequences follow, and each one catches people. First, code inside an operator runs at subscription time: maybe once, maybe once per subscriber, maybe never if nobody subscribes, and possibly on another thread (lesson 6 of this track).

Second, operators never change the object you call them on. They return a new one, so a return value you drop is a step that never happens. The second half of `AssemblyDemo` shows it:

""" + pair(J_DROP, K_DROP) + """

It prints all three orders, the 5 included. `filter` built a new, filtered `Flux`, and nobody kept it. It compiles, and it filters nothing. The fix is to subscribe to what `filter` returns.

Third, a method that returns a `Mono` can still do work before it returns, at assembly time. It looks lazy but isn't. That one gets the last section of this lesson.

**Building a chain runs nothing. Only a subscribe starts the work.**

A subscription starts the work. So what happens when two of them start it?"""

SVG = ('<svg viewBox="0 0 680 280" role="img" aria-label="A chain Flux.range, map, filter, subscriber. Assembly wraps left to right and runs nothing, like filling in a form; '
       'subscribe and request travel right to left, like signing it; data travels left to right, like the baking">'
       '<rect class="box" x="20" y="24" width="140" height="44" rx="8"/><text class="t t-code" x="90" y="51" text-anchor="middle">Flux.range</text>'
       '<rect class="box" x="190" y="24" width="130" height="44" rx="8"/><text class="t t-code" x="255" y="51" text-anchor="middle">map(...)</text>'
       '<rect class="box" x="350" y="24" width="140" height="44" rx="8"/><text class="t t-code" x="420" y="51" text-anchor="middle">filter(...)</text>'
       '<rect class="box-a" x="520" y="24" width="140" height="44" rx="8"/><text class="t t-code" x="590" y="51" text-anchor="middle">subscriber</text>'
       '<line class="ln" x1="160" y1="46" x2="186" y2="46" marker-end="url(#arr)"/>'
       '<line class="ln" x1="320" y1="46" x2="346" y2="46" marker-end="url(#arr)"/>'
       '<line class="ln" x1="490" y1="46" x2="516" y2="46" marker-end="url(#arr)"/>'
       '<text class="t-s t-m" x="340" y="112" text-anchor="middle">1. assembly, the form: each call wraps the one before it. No lambda runs.</text>'
       '<line class="ln-d" x1="40" y1="124" x2="640" y2="124" marker-end="url(#arr)"/>'
       '<text class="t-s t-a" x="340" y="172" text-anchor="middle">2. subscribe(), the signature: subscribers link up the chain, then request(n) goes up</text>'
       '<line class="ln-a" x1="640" y1="184" x2="40" y2="184" marker-end="url(#arr)"/>'
       '<text class="t-s" x="340" y="232" text-anchor="middle">3. data, the baking: onNext items flow down through map and filter to you</text>'
       '<line class="ln" x1="40" y1="244" x2="640" y2="244" marker-end="url(#arr)"/>'
       '</svg>')

# ---------------------------------------------------------------- section 2
J_COLD = """Mono<String> cake = bake("order-42");                          // cold: nothing baked yet
cake.subscribe(c -> System.out.println("shop log: " + c));     // subscription 1
String handedOver = cake.block();                              // subscription 2"""
K_COLD = """val cake: Mono<String> = bake("order-42")                    // cold: nothing baked yet
cake.subscribe { c -> println("shop log: $c") }                // subscription 1
val handedOver = cake.block()                                  // subscription 2"""
J_ONE = """String handedOver = bake("order-42")
        .doOnNext(c -> System.out.println("shop log: " + c))   // runs inside the one chain
        .block();                                             // one subscription, one cake"""
K_ONE = """val handedOver = bake("order-42")
    .doOnNext { c -> println("shop log: $c") }                // runs inside the one chain
    .block()                                                  // one subscription, one cake"""

S2 = """Most publishers you meet are **cold**: each subscriber gets its own run, from the start. `Flux.range`, `Mono.fromCallable`, a web client's response, a reactive database query: subscribe twice and the work happens twice.

That's often what you want. The `retry` operator from lesson 5 of this track works by subscribing again, and a cold source gives it a fresh attempt. And two customers who each order a cake should get two cakes.

It bites when you subscribe twice without meaning to. In `ColdDemo`, the work inside the `Mono` is baking a cake:

""" + pair(J_COLD, K_COLD) + """

`block()` is a subscription too. It subscribes and makes the calling thread wait until the value arrives. The demo printed:

```text
  oven: baking the cake for order-42 (cake #1)
shop log: cake-1
  oven: baking the cake for order-42 (cake #2)
handed to the customer: cake-2
cakes baked: 2
```

Two cakes for one order. The shop log recorded cake-1, the customer went home with cake-2, and the flour bill covers both.

This is where the order-form picture breaks. A clerk handed the same signed form twice would notice. A cold `Mono` never does: each subscription is a fresh signature, and the whole order runs again. The same thing happens when code subscribes to a `Mono` "just to log it" and then returns it to a framework that subscribes again. It happens when a test calls `block()` twice on the same `Mono`, too.

The fix is one chain, with the side effect inside it. `doOnNext` runs a side effect for each item and passes the item on unchanged:

""" + pair(J_ONE, K_ONE) + """

If several parts of a program really need one shared result, say so with `cache()` or `share()`. Those turn a cold publisher into a **hot** one, which runs once and hands its items to everyone subscribed. They have sharp edges of their own, so they get lesson 8 of this track.

**Every subscription to a cold publisher runs it again. Subscribe once, and put side effects inside the chain.**

Here is a quick test for any `Mono` you didn't write: count its subscriptions. Wrap it with `doOnSubscribe(s -> counter.incrementAndGet())`, run your code, and check the number. The lab has you build exactly that helper.

Counting finds the cake baked twice. The last trap bakes it too early, before anyone has subscribed at all."""

ASIDE = {
    "title": "What exactly does block() do, and where is it allowed?",
    "body": "`block()` subscribes, makes the calling thread wait, and returns the value. It returns `null` for an empty `Mono`, and throws if the `Mono` fails. That makes it a bridge from reactive code back to ordinary code that waits. It's the right tool at the edges: a `main` method, a test, or older blocking code that calls a reactive client. In the middle of a pipeline it defeats the point, because it ties up a thread, and lesson 6 of this track shows that some of Reactor's own threads refuse it with an exception.",
}

# ---------------------------------------------------------------- section 3
J_JUST = """Mono<String> price = Mono.just(supplier.fetchFlourPrice());   // Naive: the call runs right here"""
K_JUST = """val price: Mono<String> = Mono.just(supplier.fetchFlourPrice())   // Naive: the call runs right here"""

S3 = """`Mono.just(x)` holds a value you already have. That sounds harmless until `x` is a method call:

""" + pair(J_JUST, K_JUST) + """

Java evaluates the argument before `just` is even called. So the supplier's web service is called at assembly, on the caller's thread, exactly once. This is the cake baked while you were still writing the form.

Every later subscriber gets that same captured value, however stale it has become. If the call throws, the exception flies out of the method that builds the `Mono`, instead of arriving as `onError` where Reactor's error operators can see it. And a `retry` can never call the supplier again, because there is nothing left to run again.

`LazyDemo`, in the Try it, builds the same price `Mono` three ways and subscribes to each one twice:

```text
just          calls at assembly: 1, after 2 subscriptions: 1
fromCallable  calls at assembly: 0, after 2 subscriptions: 2
defer         calls at assembly: 0, after 2 subscriptions: 2
```

`just` called the supplier once, before anyone subscribed. The other two waited for each subscription. Those two factory methods suit different shapes of work:

| You have | Use | When it runs |
|---|---|---|
| A value already in hand | `Mono.just(value)` | at assembly, once |
| A computation that returns a value, often a blocking call | `Mono.fromCallable(() -> stock.countLoaves(kind))` | on each subscription |
| Code that returns a `Mono`, or reads state at subscribe time | `Mono.defer(() -> kitchen.book(order, ovens.nextFreeSlot()))` | on each subscription |

In Kotlin the same calls read `Mono.fromCallable { stock.countLoaves(kind) }` and `Mono.defer { kitchen.book(order, ovens.nextFreeSlot()) }`. `fromCallable` also turns the awkward cases into signals: a thrown exception becomes `onError`, and a `null` result becomes an empty `Mono`. `Mono.fromSupplier` does the same for code that throws no checked exceptions.

`defer` is for when building the publisher itself does work: picking the next free oven slot, reading the clock, choosing which kitchen to send to. Wrapping all of that in `defer` moves it to subscription time.

Two look-alikes keep the trap. `Mono.justOrEmpty(stock.countLoaves(kind))` handles `null`, but its argument is still evaluated at once. And `Mono.fromFuture(future)` takes a `CompletableFuture` that is already running when you pass it in. Use the `Supplier` overload, `Mono.fromFuture(() -> client.sendAsync(request))`, to start a new one for each subscription.

**`Mono.just` takes a value, not a job. Give jobs to `fromCallable` or `defer`.**"""

# ---------------------------------------------------------------- closing
CLOSING = """We started with an order form for a cake, and Reactor behaves just like one. Building a chain fills in the form, `subscribe` signs it, and every signature on a cold publisher bakes a fresh cake. `Mono.just(call())` is the one cake baked before the form was even finished.

Now look in your own code for `Mono.just(` or `Flux.just(` with a method call inside the parentheses, and for a `Mono` that is both subscribed and returned.

Next, we'll add stations to the belt. `map` changes each item as it passes. What happens when a station has to call something slow, and its function returns a `Mono`?"""

# ---------------------------------------------------------------- compare, worked, drill
CJ = """// eager: fetchFlourPrice runs here, once, before just() is called
Mono<String> eager = Mono.just(supplier.fetchFlourPrice());

// lazy: the lambda runs on every subscription
Mono<String> lazy = Mono.fromCallable(() -> supplier.fetchFlourPrice());

// lazy: build a whole publisher per subscription
Mono<Booking> booking = Mono.defer(() -> kitchen.book(order, ovens.nextFreeSlot()));"""
CK = """// eager: fetchFlourPrice runs here, once, before just() is called
val eager: Mono<String> = Mono.just(supplier.fetchFlourPrice())

// lazy: the lambda runs on every subscription
val lazy: Mono<String> = Mono.fromCallable { supplier.fetchFlourPrice() }

// lazy: build a whole publisher per subscription
val booking: Mono<Booking> = Mono.defer { kitchen.book(order, ovens.nextFreeSlot()) }

// lazy, written as a coroutine (kotlinx-coroutines-reactor): the block starts on each subscription
val bookingCo: Mono<Booking> = mono { kitchen.bookSuspending(order, ovens.nextFreeSlot()) }"""
W0J = """Mono<Booking> book(CakeOrder order) {
    Slot slot = ovens.nextFreeSlot();                    // reads the oven schedule right now
    log.info("booking {} into {}", order.cake(), slot);
    return kitchen.book(order, slot);                    // a cold Mono: books on subscribe
}"""
W0K = """fun book(order: CakeOrder): Mono<Booking> {
    val slot = ovens.nextFreeSlot()                      // reads the oven schedule right now
    log.info("booking {} into {}", order.cake, slot)
    return kitchen.book(order, slot)                     // a cold Mono: books on subscribe
}"""
W2J = """Mono<Booking> book(CakeOrder order) {
    return Mono.defer(() -> {
        Slot slot = ovens.nextFreeSlot();                // 1. per attempt
        log.info("booking {} into {}", order.cake(), slot);   // 2. per attempt
        return kitchen.book(order, slot);                // 3. the cold call
    });
}"""
W2K = """fun book(order: CakeOrder): Mono<Booking> =
    Mono.defer {
        val slot = ovens.nextFreeSlot()                  // 1. per attempt
        log.info("booking {} into {}", order.cake, slot) // 2. per attempt
        kitchen.book(order, slot)                        // 3. the cold call
    }"""
W3J = """Mono<Booking> m = bakery.book(order);
assertThat(ovens.lookups()).isZero();       // nothing at assembly
m.block();
m.block();
assertThat(ovens.lookups()).isEqualTo(2);   // once per subscription"""
W3K = """val m = bakery.book(order)
assertThat(ovens.lookups()).isZero()        // nothing at assembly
m.block()
m.block()
assertThat(ovens.lookups()).isEqualTo(2)    // once per subscription"""
DJ = """Mono<Integer> loavesLeft(String kind) {
    return Mono.fromCallable(() -> stock.countLoaves(kind));
}

// proof: a counting fake stock room
AtomicInteger calls = new AtomicInteger();
Stock stock = kind -> { calls.incrementAndGet(); return null; };
Mono<Integer> m = new Shelf(stock).loavesLeft("spelt");
assert calls.get() == 0;            // lazy
assert m.block() == null;           // empty Mono: block() returns null
assert calls.get() == 1;            // one call per subscription"""
DK = """fun loavesLeft(kind: String): Mono<Int> =
    Mono.fromCallable { stock.countLoaves(kind) }      // a null result becomes an empty Mono

// proof: a counting fake stock room (fun interface Stock { fun countLoaves(kind: String): Int? })
val calls = AtomicInteger()
val stock = Stock { calls.incrementAndGet(); null }
val m = Shelf(stock).loavesLeft("spelt")
check(calls.get() == 0)        // lazy
check(m.block() == null)       // empty Mono: block() returns null
check(calls.get() == 1)        // one call per subscription"""

L = {
 "id": "rx-02",
 "title": "Mono and Flux: nothing happens until you subscribe",
 "minutes": 35,
 "goal": "By the end you can tell assembly time from subscription time, predict how many times a cold `Mono` or `Flux` does its work, and choose between `Mono.just`, `fromCallable` and `defer`.",
 "opening": OPENING,
 "warmup": {
  "q": "How many times does this code ask the supplier for the price of flour?\n\n```java\nMono<String> price = Mono.just(supplier.fetchFlourPrice());\nprice.block();\nprice.block();\n```",
  "options": [
   "Zero: nothing happens until you subscribe",
   "Once, while the Mono is being built",
   "Twice, once per block()",
   "Three times: once to build it and once per block()"
  ],
  "answer": 1,
  "why": "Java evaluates `supplier.fetchFlourPrice()` before `Mono.just` is even called, so the call happens while the `Mono` is being built, once. `Mono.just` then hands that same value to every subscriber. \"Nothing happens until you subscribe\" is true for the code inside operators, not for arguments you evaluate yourself."
 },
 "sections": [
  {
   "h": "Flux for many items, Mono for one or none",
   "body": S0,
   "try": {
    "title": "Watch the signals go by",
    "minutes": 4,
    "steps": [
     "Read `FirstFluxDemo`. It subscribes to a `Flux` of three loaves with `log()` in the chain, then to a failing `Mono` with no error callback.",
     "Predict the order of the lines, including the `log()` lines. What happens to the \"out of flour\" error?",
     "Run it. Then add an error lambda to the second `subscribe` and run it again."
    ],
    "code": demo("FirstFluxDemo"),
    "expect": "`log()` prints `onSubscribe`, then `request(unbounded)`, then each `onNext` followed by your `got ...` line, then `onComplete()` and `done`: the protocol from the last lesson, live. The failing `Mono` prints `main carries on` and an `[ERROR] ... Operator called default onErrorDropped - reactor.core.Exceptions$ErrorCallbackNotImplemented: java.lang.IllegalStateException: out of flour` log line. The two may appear in either order, since the log goes to a different output stream. Nothing is thrown at `main`. With an error lambda, your lambda prints the failure and the ERROR line is gone."
   }
  },
  {
   "h": "Assembly fills in the form, subscribe starts the baking",
   "body": S1,
   "figure": {"svg": SVG, "caption": "Three passes over the same chain: assembly runs no code of yours, subscription travels up to the source, data travels down to you."},
   "try": {
    "title": "Count what runs, and when",
    "minutes": 3,
    "steps": [
     "`AssemblyDemo` counts how often `map` runs, before and after `subscribe`. Then it filters a list of order sizes.",
     "Predict both counts and the orders printed. Run it.",
     "Fix the filter so that only orders above 10 loaves print."
    ],
    "code": demo("AssemblyDemo"),
    "expect": "`after assembly: map ran 0 times`, three prices, then `after subscribe: map ran 3 times`. All three orders print, 5 included, because `orderSizes.filter(...)` returned a new `Flux` that nobody used. The fix is to subscribe to the result: `orderSizes.filter(loaves -> loaves > 10).subscribe(...)` in Java, `orderSizes.filter { it > 10 }.subscribe { ... }` in Kotlin."
   },
   "refs": [{"title": "Reactor reference: Introduction to reactive programming (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc", "kind": "docs"}]
  },
  {
   "h": "Cold publishers do their work again for every subscriber",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "Bake one cake twice by accident",
    "minutes": 4,
    "steps": [
     "`ColdDemo` builds one baking `Mono`, subscribes once for the shop log, and once with `block()` for the customer.",
     "Predict how many cakes the oven bakes. Run it.",
     "Rewrite `main` as one chain: `cake.doOnNext(c -> System.out.println(\"shop log: \" + c)).block()` in Java, or `cake.doOnNext { println(\"shop log: $it\") }.block()` in Kotlin. Run it again."
    ],
    "code": demo("ColdDemo"),
    "expect": "The first run prints two `oven: baking the cake for order-42` lines. The shop log shows `cake-1`, the customer gets `cake-2`, and the last line is `cakes baked: 2`. The log and the customer don't even agree on which cake was sold. With one chain there is one cake, and the shop log and the customer see the same one."
   }
  },
  {
   "h": "Mono.just is eager; fromCallable and defer are lazy",
   "body": S3,
   "try": {
    "title": "just, fromCallable, defer",
    "minutes": 3,
    "steps": [
     "`LazyDemo` builds the same flour-price `Mono` three ways and subscribes to each twice.",
     "Before running, fill in a small table: calls at assembly, and calls after two subscriptions, for each of the three.",
     "Run it and compare. Then change the `defer` line to use `Mono.justOrEmpty(fetchFlourPrice())` inside the `defer`. Does that change anything?"
    ],
    "code": demo("LazyDemo"),
    "expect": "`just`: 1 call at assembly, still 1 after two subscriptions. `fromCallable` and `defer`: 0 at assembly, 2 after two subscriptions. `justOrEmpty` inside `defer` is still lazy, because `defer` delays the whole lambda, argument included. Outside `defer`, `justOrEmpty(fetchFlourPrice())` would be eager like `just`."
   },
   "refs": [{"title": "Reactor reference: Hot versus cold (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/reactor-hotCold.adoc", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "Eager and lazy Monos in Java and Kotlin",
  "java": {"title": "Prices.java", "src": CJ},
  "kotlin": {"title": "Prices.kt", "src": CK},
  "note": "The calls are the same Reactor API in both languages, and so is the trap, because it is plain argument evaluation: Kotlin evaluates `supplier.fetchFlourPrice()` before `Mono.just` runs, exactly like Java. Kotlin's trailing lambdas make the lazy forms shorter (`Mono.fromCallable { ... }`). The `kotlinx-coroutines-reactor` library adds `mono { }`, a cold `Mono` whose body is a coroutine: it starts on each subscription, and a `null` result gives an empty `Mono`. That's handy when Kotlin code has to hand a `Mono` to Java code. Kotlin's own `Flow` has the same trap under other names: `flowOf(call())` is eager, and `flow { emit(call()) }` is lazy."
 },
 "worked": {
  "title": "Make a booking method lazy",
  "steps": [
   {"say": "This method books a cake order into a slot in the oven schedule and sends the booking to the kitchen's program. It returns a `Mono`, so it looks lazy. Mark which lines run when `book(order)` is called, and which run on subscribe.",
    "code": W0J, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "The slot lookup and the log line run at call time, once. Only the booking runs on subscribe. Now add `.retry(2)` at the call site, because the kitchen's program sometimes fails. Say the first attempt fails because another order took that slot a moment earlier. Each retry subscribes again to `kitchen.book(order, slot)` with the same, already taken slot. All three attempts fail with \"slot taken\", and the log shows one \"booking\" line for three attempts.", "code": "", "lang": ""},
   {"say": "Move the whole body into `defer`. Now every subscription, every retry included, looks up a fresh slot, logs again and books again.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Check it with a counter, the way the lab does: build the `Mono`, check that there were no slot lookups, subscribe twice, and check that there were two. A test like this catches the next person who \"simplifies\" the method back to the eager version.",
    "code": W3J, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Make an eager lookup lazy, and count subscriptions",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/OrderLookup.java", f"{lab}/main/{P}/OrderBook.java", f"{lab}/main/{P}/Subscriptions.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l02.*'",
  "steps": [
   "Read `OrderBook`, a slow client for the bakery's order book, which lives in another program. `fetchStatus` returns an order's status, such as `\"READY\"`, or `null` for an order it doesn't know. You don't change this file.",
   "Run the tests. All six fail. Read the messages: the order book is called while the `Mono` is being built, a failure is thrown instead of signalled, and `take(2)` still costs five calls.",
   "Rewrite `OrderLookup.status` so that the order book is called on each subscription. Pick the factory that also turns `null` into an empty `Mono`.",
   "Rewrite `OrderLookup.statuses` so each order is looked up only when the subscriber asks for it. You need two operators.",
   "Write `Subscriptions.counted`: return a `Mono` that adds one to the counter every time something subscribes, and leaves the values alone. Run the tests until all six pass."
  ],
  "hints": [
   "`Mono.fromCallable(() -> book.fetchStatus(orderId))` does all three jobs: it's lazy, it turns an exception into `onError`, and it turns `null` into empty.",
   "`Flux.fromIterable(ids)` emits the ids lazily. `.map(book::fetchStatus)` then calls the order book once per id, as each one is requested. `take(2)` requests only two.",
   "`doOnSubscribe` runs a side effect once per subscription. `Mono.defer(() -> { counter.incrementAndGet(); return source; })` works too."
  ],
  "done_when": "All six tests in `LazinessTest` pass."
 },
 "drill": {
  "title": "Wrap a blocking lookup, from memory",
  "minutes": 4,
  "prompt": "Close this page. `stock.countLoaves(kind)` is a blocking call that returns an `Integer`, or `null` when the bakery doesn't sell that kind of bread. Write `Mono<Integer> loavesLeft(String kind)` so that it is lazy, calls the stock room once per subscription, and turns `null` into an empty `Mono`. Then write three lines that prove it with an `AtomicInteger`.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`Flux` is 0 to N items, `Mono` is 0 or 1. Both are Reactive Streams publishers, and neither may emit `null`.",
  "Assembly only builds a chain of wrapper objects, like filling in an order form. Your lambdas run at subscription time, once per subscriber, possibly never.",
  "Operators return new instances. An operator whose result you drop is not part of any chain.",
  "Cold publishers run again for every subscriber, and `block()` counts as one. Two subscriptions to a baking `Mono` bake two cakes.",
  "`Mono.just(call())` runs `call()` at assembly, once. Use `fromCallable` for a value and `defer` for code that builds a publisher.",
  "Always give `subscribe` an error callback. The limit of today's tools: a cold publisher can't share one run between subscribers; that takes `cache()` or `share()`, with traps of their own (lesson 8)."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "What does this print?\n\n```java\nFlux<String> f = Flux.just(\"rye\", \"spelt\")\n        .map(s -> { System.out.println(\"map \" + s); return s.toUpperCase(); });\nSystem.out.println(\"built\");\n```",
   "options": ["`map rye`, `map spelt`, `built`", "`built` only", "`built`, `map rye`, `map spelt`", "Nothing"],
   "answer": 1,
   "why": "Building the chain stores the lambda without calling it. Nobody subscribes to `f`, so `map` never runs and only `built` prints. The tempting first option is how a loop over a list would behave; here nothing ever subscribes."},
  {"q": "`oven.bake(order)` returns a cold `Mono<Cake>` built with `fromCallable`. A handler does `Mono<Cake> c = oven.bake(order); c.subscribe(log::record); return c.block();`. How many cakes does the oven bake?",
   "options": ["Two, one per subscription", "One, because both use the same `Mono` object", "Zero, because `subscribe` and `block` cancel each other", "It depends on which thread runs first"],
   "answer": 0,
   "why": "A cold publisher runs once per subscriber, and `subscribe` and `block` are two subscriptions, so the callable runs twice. Sharing a `Mono` object shares the order form, not the cake. Put the log in the chain with `doOnNext`, or use `cache()` if you really need to share a result."},
  {"q": "`stock.countLoaves(kind)` is a blocking call that may return `null`. Which line gives a lazy `Mono` that makes the call on each subscription and is empty on `null`?",
   "options": ["`Mono.just(stock.countLoaves(kind))`", "`Mono.justOrEmpty(stock.countLoaves(kind))`", "`Flux.just(stock.countLoaves(kind)).next()`", "`Mono.fromCallable(() -> stock.countLoaves(kind))`"],
   "answer": 3,
   "why": "`fromCallable` calls the lambda on each subscription, and turns `null` into empty and exceptions into `onError`. `justOrEmpty` handles `null` too, but `stock.countLoaves(kind)` is still an argument evaluated at assembly. `Mono.just(null)` would throw."},
  {"q": "You subscribe to `Mono.error(new IllegalStateException(\"out of flour\"))` with only an `onNext` lambda. What happens?",
   "options": ["The exception is thrown out of `subscribe` to your code", "Nothing at all: errors without a handler are ignored silently", "Reactor logs `ErrorCallbackNotImplemented` at ERROR level, and your code carries on", "The JVM prints a stack trace and exits"],
   "answer": 2,
   "why": "With no error callback, Reactor hands the error to its `onErrorDropped` hook, which logs it at ERROR level. Your thread carries on undisturbed. That's why a test with no check on the error can pass even though the stream failed."},
  {"q": "From \"Why reactive: push, pull and backpressure\": you call `flux.subscribe(item -> box(item))` with just the one lambda. What demand does that subscriber send to the source?",
   "options": ["`request(1)` before each item", "`request(Long.MAX_VALUE)`: unbounded", "`request(256)`, then more in batches", "No request until the first item arrives"],
   "answer": 1,
   "why": "The lambda form of `subscribe` requests everything, which `log()` shows as `request(unbounded)`. That is rule 3.17's unbounded demand: no backpressure from this subscriber. Lesson 7 of this track shows how operators like `limitRate` turn it back into bounded requests.",
   "from": "rx-01"}
 ],
 "flashcards": [
  {"front": "When does the lambda inside `flux.map(...)` run?", "back": "At subscription time, once per item for each subscriber. Never at assembly, and never if nobody subscribes."},
  {"front": "`Mono.just(fetch())` is subscribed three times. How many times does `fetch()` run?", "back": "Once, at assembly, before `just` is even called. All three subscribers get the same value."},
  {"front": "What does `Mono.fromCallable` do with a thrown exception and with a `null` result?", "back": "The exception becomes `onError`. `null` becomes an empty `Mono` (just `onComplete`)."},
  {"front": "What is a cold publisher?", "back": "One that does its work again, from the start, for every subscriber. Most Reactor sources are cold."},
  {"front": "`orderSizes.filter(n -> n > 10);` on its own line, then `orderSizes.subscribe(...)`. Is anything filtered?", "back": "No. Operators return a new `Flux`. The filtered one was thrown away, so `orderSizes` is unchanged."},
  {"front": "When do you pick `Mono.defer` over `Mono.fromCallable`?", "back": "When the code returns a `Mono` (or another publisher), or must read state at subscription time, such as the next free slot or the clock."}
 ],
 "terms": [
  {"term": "Flux", "plain": "A Reactor publisher of 0 to N items, which may end with complete or error."},
  {"term": "Mono", "plain": "A Reactor publisher of at most one item. `Mono<Void>` only signals completion or error."},
  {"term": "Operator", "plain": "A method like `map` or `filter` that wraps a publisher and returns a new one with one more step."},
  {"term": "Assembly time", "plain": "When you call operators to build the chain. Only wrapper objects are created; none of your lambdas run."},
  {"term": "Subscription time", "plain": "When `subscribe` (or `block`) is called. The chain is linked up, demand goes up, and the source starts."},
  {"term": "Cold publisher", "plain": "A publisher that does its work again for each subscriber."},
  {"term": "Hot publisher", "plain": "A publisher that runs once and shares its items with whoever is subscribed (lesson 8 of this track)."}
 ],
 "explain_back": {
  "prompt": "A teammate wrapped a flaky call as `Mono.just(supplier.fetchFlourPrice()).retry(3)` and is puzzled that the logs show only one attempt. Explain in your own words what is going on, and how to fix it.",
  "answer": "`supplier.fetchFlourPrice()` is an argument to `Mono.just`, so Java runs it once, right there, before any `Mono` exists. If it throws, the exception leaves the method before `retry` is even attached. If it returns, `Mono.just` holds that one value, and every subscription gets it again. `retry` works by subscribing again, and subscribing again to `just` runs nothing new. Wrapping the call as `Mono.fromCallable(() -> supplier.fetchFlourPrice())`, or `Mono.defer(...)` if the client already returns a `Mono`, moves the call to subscription time. Then each retry makes a real new attempt, and failures arrive as `onError`, where `retry` can see them."
 },
 "deeper": {
  "minutes": 8,
  "body": "Two more eager traps look like the `Mono.just` one, and one pair of methods is easy to mix up.\n\n**`Flux.fromStream(stream)`.** A Java `Stream` can only be used once. The first subscriber drains it, and the second gets `IllegalStateException: stream has already been operated upon or closed`. Use the supplier overload, `Flux.fromStream(() -> orders.streamToday())`, so each subscription gets a fresh stream. `Flux.fromIterable(list)` is fine to subscribe to many times, because a `List` can be walked again.\n\n**`Mono.fromFuture(future)`.** A `CompletableFuture` stands for work that has already started. `Mono.fromFuture(client.sendAsync(request))` sends the request at assembly, and a retry subscribes again to the same finished future. `Mono.fromFuture(() -> client.sendAsync(request))` starts a new request for each subscription. This is the bridge you'll use most often from code built with the executors track's `CompletableFuture` methods.\n\n**`fromCallable` and `fromSupplier`.** The first accepts code that throws checked exceptions, because a `Callable` may throw `Exception`. The second does not. Both are lazy, and both treat `null` as empty."
 },
 "sources": [
  {"title": "Reactor reference: Introduction to reactive programming (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc"},
  {"title": "Reactor reference: Flux, an asynchronous sequence of 0-N items (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/flux.adoc"},
  {"title": "Reactor reference: Mono, an asynchronous 0-1 result (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/mono.adoc"},
  {"title": "Reactor reference: Hot versus cold (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/reactor-hotCold.adoc"}
 ]
}
out = ROOT / "content/lessons/rx-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
