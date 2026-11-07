import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l09"
K = "kotlin/workbench/patterns/l09"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l09.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 700 232" role="img" aria-label="A request passes logging, auth, idempotency and fraud before the charge. Auth can answer 401, idempotency 409 and fraud review, and the response travels back out through every step">
<rect class="box" x="10" y="40" width="80" height="46" rx="8"/>
<text class="t" x="50" y="68" text-anchor="middle">request</text>
<rect class="box" x="110" y="40" width="96" height="46" rx="8"/>
<text class="t" x="158" y="68" text-anchor="middle">logging</text>
<rect class="box" x="230" y="40" width="80" height="46" rx="8"/>
<text class="t" x="270" y="68" text-anchor="middle">auth</text>
<rect class="box" x="334" y="40" width="120" height="46" rx="8"/>
<text class="t" x="394" y="68" text-anchor="middle">idempotency</text>
<rect class="box" x="478" y="40" width="84" height="46" rx="8"/>
<text class="t" x="520" y="68" text-anchor="middle">fraud</text>
<rect class="box-a" x="586" y="40" width="96" height="46" rx="8"/>
<text class="t" x="634" y="68" text-anchor="middle">charge</text>
<line class="ln-a" x1="90" y1="63" x2="106" y2="63" marker-end="url(#arr)"/>
<line class="ln-a" x1="206" y1="63" x2="226" y2="63" marker-end="url(#arr)"/>
<line class="ln-a" x1="310" y1="63" x2="330" y2="63" marker-end="url(#arr)"/>
<line class="ln-a" x1="454" y1="63" x2="474" y2="63" marker-end="url(#arr)"/>
<line class="ln-a" x1="562" y1="63" x2="582" y2="63" marker-end="url(#arr)"/>
<line class="ln-bad" x1="270" y1="86" x2="270" y2="128" marker-end="url(#arr)"/>
<rect class="box-bad" x="230" y="132" width="80" height="36" rx="8"/>
<text class="t t-code" x="270" y="155" text-anchor="middle">401</text>
<line class="ln-bad" x1="394" y1="86" x2="394" y2="128" marker-end="url(#arr)"/>
<rect class="box-bad" x="354" y="132" width="80" height="36" rx="8"/>
<text class="t t-code" x="394" y="155" text-anchor="middle">409</text>
<line class="ln" x1="520" y1="86" x2="520" y2="128" marker-end="url(#arr)"/>
<rect class="box-b" x="470" y="132" width="100" height="36" rx="8"/>
<text class="t" x="520" y="155" text-anchor="middle">review</text>
<line class="ln-d" x1="634" y1="86" x2="634" y2="196"/>
<line class="ln-d" x1="634" y1="196" x2="158" y2="196"/>
<line class="ln-d" x1="158" y1="196" x2="158" y2="90" marker-end="url(#arr)"/>
<text class="t-s t-m" x="400" y="220" text-anchor="middle">the response travels back out through every step</text>
</svg>""".replace("\n", "")

S1 = """A payment moves from `Created` to `Authorized` to `Captured`, maybe to `Refunded`, and can end in `Failed`. The GoF State pattern gives each state its own class with one method per event: `CreatedState.capture()` throws, `AuthorizedState.capture()` returns a `CapturedState`. That is five classes with four methods each, and the rules for one transition live wherever its class happens to be.

Java 21 and Kotlin let you write states and events as data and the rules as one function:

```java
sealed interface PaymentState permits Created, Authorized, Captured, Refunded, Failed {}
record Created(String id) implements PaymentState {}
record Authorized(String id, String authCode, long amount) implements PaymentState {}
record Captured(String id, long amount) implements PaymentState {}
record Refunded(String id, long amount) implements PaymentState {}
record Failed(String id, String reason) implements PaymentState {}

sealed interface PaymentEvent permits Authorize, Capture, Refund, Decline {}
record Authorize(String authCode, long amount) implements PaymentEvent {}
record Capture() implements PaymentEvent {}
record Refund(long amount) implements PaymentEvent {}
record Decline(String reason) implements PaymentEvent {}

static PaymentState transition(PaymentState s, PaymentEvent e) {
    return switch (s) {                                  // no default: a new state breaks the build
        case Created c -> switch (e) {
            case Authorize(var code, var amt) when amt > 0 -> new Authorized(c.id(), code, amt);
            case Decline(var reason) -> new Failed(c.id(), reason);
            default -> throw illegal(s, e);
        };
        case Authorized a -> switch (e) {
            case Capture() -> new Captured(a.id(), a.amount());
            case Decline(var reason) -> new Failed(a.id(), reason);
            default -> throw illegal(s, e);
        };
        case Captured(var id, var amt) -> switch (e) {
            case Refund(var r) when r > 0 && r <= amt -> new Refunded(id, r);
            default -> throw illegal(s, e);
        };
        case Refunded r -> throw illegal(s, e);          // terminal
        case Failed f -> throw illegal(s, e);            // terminal
    };
}
```

```kotlin
sealed interface PaymentState {
    data class Created(val id: String) : PaymentState
    data class Authorized(val id: String, val authCode: String, val amount: Long) : PaymentState
    data class Captured(val id: String, val amount: Long) : PaymentState
    data class Refunded(val id: String, val amount: Long) : PaymentState
    data class Failed(val id: String, val reason: String) : PaymentState
}
sealed interface PaymentEvent {
    data class Authorize(val authCode: String, val amount: Long) : PaymentEvent
    data object Capture : PaymentEvent
    data class Refund(val amount: Long) : PaymentEvent
    data class Decline(val reason: String) : PaymentEvent
}

fun transition(s: PaymentState, e: PaymentEvent): PaymentState = when (s) {   // no else
    is PaymentState.Created -> when (e) {
        is PaymentEvent.Authorize if e.amount > 0 -> PaymentState.Authorized(s.id, e.authCode, e.amount)
        is PaymentEvent.Decline -> PaymentState.Failed(s.id, e.reason)
        else -> throw illegal(s, e)
    }
    is PaymentState.Authorized -> when (e) {
        PaymentEvent.Capture -> PaymentState.Captured(s.id, s.amount)
        is PaymentEvent.Decline -> PaymentState.Failed(s.id, e.reason)
        else -> throw illegal(s, e)
    }
    is PaymentState.Captured -> when (e) {
        is PaymentEvent.Refund if e.amount in 1..s.amount -> PaymentState.Refunded(s.id, e.amount)
        else -> throw illegal(s, e)
    }
    is PaymentState.Refunded, is PaymentState.Failed -> throw illegal(s, e)    // terminal
}
```

Read it as a table. Each outer case is a state, each inner case is an event that state accepts, and everything else is illegal. Record patterns take fields out where you need them (`Captured(var id, var amt)`), and guards state what an event requires (`when amt > 0`). Kotlin's guards in `when` (`is Refund if ...`) became stable in Kotlin 2.2.0.

The function is pure: old state and event in, new state out, no I/O. You test it without mocks, and replaying history is one fold: `val current: PaymentState = events.fold(Created(id), ::transition)`, which is how the lab's `replay` works. Keep side effects out of it. If capturing needs the PSP, call the PSP first and feed its answer in as an event."""

S2 = """Chargebacks arrive, and a captured payment now needs a `Disputed` state. Add the record to the sealed interface and compile, before you write a single rule:

```text
javac:   error: the switch expression does not cover all possible input values
kotlinc: error: 'when' expression must be exhaustive. Add the 'is Disputed' branch or an 'else' branch.
```

Every switch over the state type fails, and each error points at one place: the transition function, the status label in the API, the metrics tag, the admin screen. The compiler has written your to-do list. Work through it, and the feature is done when the build is green.

That only works if you leave room for it. A `default` (or `else`) on a switch over your own sealed type means \"and anything else\", and the compiler believes you: `Disputed` falls into the default without a word. The inner switches in `transition` do use `default`, on purpose. Most (state, event) pairs are illegal, and listing each illegal pair adds nothing. So the rule is narrower than \"never write default\": never write it on the dimension you expect to grow. States grow. Here, the events within one state mostly don't.

The check happens at compile time, so there is a gap at run time, which Brian Goetz's design notes call the remainder: `null`, and subtypes added after the switch was compiled. A switch on a null state throws `NullPointerException`. If a new subtype arrives from a separately compiled jar, Java throws `MatchException` and Kotlin throws `NoWhenBranchMatchedException`. You don't write code for those cases, but a deploy that mixes old and new jars can hit them.

State and Strategy have the same structure: an object holds a value and behavior depends on it. The difference is who chooses. The caller picks a strategy, and it stays. A state machine picks its own next state as events arrive."""

S3 = """A payment request passes logging, authentication, an idempotency check and fraud screening before any code charges the card. Each step may answer on its own (401, 409, \"send to review\") or pass the request on. That is **Chain of Responsibility**, and you use it every day. A servlet `Filter` gets the request and a `FilterChain`, and uses the chain \"to invoke the next filter in the chain\". OkHttp's `Interceptor` has one method, `intercept(chain)`, and calls `chain.proceed(request)` to continue.

Each link is a function of the request and `next`, the rest of the chain:

```java
Interceptor auth = (r, next) -> r.headers().containsKey("Authorization")
        ? next.proceed(r)                              // pass it on
        : new Response(401, "no token");               // answer now: the rest never runs

Interceptor logging = (r, next) -> {
    Response res = next.proceed(r);                    // what follows runs on the way out
    log.info(r.path() + " -> " + res.status());
    return res;
};

Chain pipeline = chain(List.of(logging, auth, idempotency, fraud), chargeHandler);
```

```kotlin
val auth = Interceptor { r, next ->
    if ("Authorization" in r.headers) next(r)          // pass it on
    else HttpResponse(401, "no token")                 // answer now: the rest never runs
}

val logging = Interceptor { r, next ->
    next(r).also { log.info("${r.path} -> ${it.status}") }   // runs on the way out
}

val pipeline = chain(listOf(logging, auth, idempotency, fraud), chargeHandler)
```

Code before `next` runs on the way in, code after it runs on the way out with the response, and not calling `next` at all is a short-circuit. Logging wraps everything; auth can stop a request before any later step sees it.

The GoF version links handler objects with `setNext()`. You don't need that. A list of functions and a fold make the chain, as the comparison below shows, and the result is immutable, so one pipeline serves every request on every thread. The lab's `FraudChain.build` copies the list it is given for the same reason: a later edit to the caller's list must not change a chain that is already in use."""

S4 = """Chains fail in four ways, and each looks like a bug somewhere else.

Order. Interceptors run in list order, and order is behavior. Put the idempotency check before auth, and a request rejected for a missing token has already used up its idempotency key, so the client's corrected retry gets 409 and the customer is never charged. Put logging after auth, and rejected requests never reach your logs. Pin the order with a test.

Forgetting `next`. A handler that returns without calling `next` and without a real answer drops the request silently. In a servlet filter, the client gets an empty 200. Every path through a handler must either call `next` or return a deliberate response.

Calling `next` twice. A retry wrapped around `next.proceed(r)` at the front of the chain repeats everything after it: the fraud check, the idempotency check and the charge. Put retries as close as possible to the call they retry, around the PSP client, not around the pipeline.

Exceptions. When a later handler throws, the code after `next.proceed(r)` in earlier handlers never runs. Timers, MDC cleanup (removing the request's entries from the logger's per-thread context map) and metrics belong in `finally`.

The same shape runs your Quarkus services. A CDI interceptor's `@AroundInvoke` method calls `InvocationContext.proceed()` to continue, and JAX-RS filters and CDI interceptors are ordered by `@Priority`. When a filter seems not to run, check its priority before you read its code.

Check yourself. In the pipeline from the last section, `fraud` throws for one request. Does that request get a line from `logging`, which is first in the list? (No. `logging` writes its line after `next.proceed(r)` returns, and that call never returns. Wrap `next.proceed(r)` in `try`/`finally` and log in the `finally`, and the request shows up, with the exception still on its way out.)"""

L = {
 "id": "pat-09",
 "title": "State and Chain of Responsibility",
 "minutes": 37,
 "goal": "By the end you can model a payment lifecycle as sealed states, sealed events and one pure transition function, use the compiler's exhaustiveness errors as a to-do list, and build an interceptor chain whose order, short-circuits and exceptions you control.",
 "warmup": {
  "q": "A payment state machine is a `switch` over a sealed `PaymentState` with `case` branches for all five states and no `default`. You add a sixth record, `Disputed`, to the sealed interface. What happens when you build?",
  "options": ["It compiles; `Disputed` payments go to the first matching case", "It compiles; `Disputed` payments throw `MatchException` at runtime", "It fails to compile at every switch over `PaymentState` that has no default", "It fails only if a test calls the switch with a `Disputed` value"],
  "answer": 2,
  "why": "A switch expression over a sealed type must cover every permitted subtype, and with no `default` there is nothing to catch the new one, so javac reports \"the switch expression does not cover all possible input values\" at each switch. That list of errors is exactly the list of places that need a rule. `MatchException` only appears when a subtype arrives from code compiled separately after the switch."
 },
 "sections": [
  {
   "h": "State as data: a payment lifecycle in sealed types",
   "body": S1,
   "try": {
    "title": "Walk a payout through its states",
    "minutes": 4,
    "steps": [
     "Open `PayoutStateDemo.java` (or `.kt`): a merchant payout with the same shape as the payment above. Predict the five lines.",
     "Run it with the command below.",
     "Change the approver from `\"dana\"` to `\" \"` (a blank name). Predict where the program stops and what it prints, then run."
    ],
    "code": code("java", "PayoutStateDemo.java", "PayoutStateDemo", "kotlin", "PayoutStateDemo.kt", "PayoutStateDemoKt"),
    "expect": "`pending approval`, `approved by dana`, `sent, bank ref DE-REF-0091`, `settled`, then `rejected: Send not allowed in Requested`. With a blank approver, the guard `when !who.isBlank()` fails, the event falls to the inner `default`, and the program stops at the first event with `IllegalStateException: Approve not allowed in Requested`. The guard is part of the rule, not a separate check."
   },
   "refs": [
    {"title": "JEP 441: Pattern matching for switch", "url": "https://openjdk.org/jeps/441", "kind": "read"},
    {"title": "What's new in Kotlin 2.2.0 (guards in when)", "url": "https://kotlinlang.org/docs/whatsnew22.html", "kind": "docs"}
   ]
  },
  {
   "h": "Let the compiler keep the to-do list",
   "body": S2,
   "try": {
    "title": "Add a state and read the errors",
    "minutes": 4,
    "steps": [
     "In `PayoutStateDemo.java`, add `record OnHold(String id, long amountMinor) implements PayoutState {}` and add `OnHold` to the `permits` list. In Kotlin, add `data class OnHold(val id: String, val amountMinor: Long) : PayoutState` inside the sealed interface.",
     "Build it with the demo command. Before you look, predict how many errors you'll get and where.",
     "Fix them: in `next`, an on-hold payout accepts nothing yet (`throw illegal(s, e)`); in `label`, return `\"on hold\"`. Build again, then remove `OnHold`."
    ],
    "code": code("java", "PayoutStateDemo.java", "PayoutStateDemo", "kotlin", "PayoutStateDemo.kt", "PayoutStateDemoKt"),
    "expect": "Two errors, one per switch over the state: `next` and `label`. javac says `the switch expression does not cover all possible input values` twice; kotlinc says `'when' expression must be exhaustive. Add the 'is OnHold' branch or an 'else' branch.` twice. Adding the two branches makes the build green: the compiler's list was complete."
   },
   "refs": [
    {"title": "Exhaustiveness, unconditionality and remainder (Goetz and Bierman)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md", "kind": "read"}
   ]
  },
  {
   "h": "Chain of Responsibility: pass it on, or answer now",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Each step either passes the request on or answers it. The response comes back out through every step it passed, so logging sees all of them."},
   "try": {
    "title": "Reorder two interceptors",
    "minutes": 5,
    "steps": [
     "Read `FilterChainDemo.java` (or `.kt`). The third request has no token; the fourth is the client's fixed retry with the same idempotency key. Predict the four responses and the number of charges.",
     "Run it with the command below.",
     "Swap `auth` and `idempotency` in the list (`List.of(logging, idempotency, auth)`). Predict the last two responses and `charges`, then run."
    ],
    "code": code("java", "FilterChainDemo.java", "FilterChainDemo", "kotlin", "FilterChainDemo.kt", "FilterChainDemoKt"),
    "expect": "In order: 200 charged, 409 duplicate (the same key again), 401 no token, 200 charged, and `charges: 2`; logging prints a line for every request, rejected ones included. After the swap, the 401 request records its key before auth rejects it, so the fixed retry gets `409 duplicate` and `charges: 1`: the customer's payment never goes through."
   },
   "refs": [
    {"title": "Jakarta Servlet FilterChain (source)", "url": "https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/FilterChain.java", "kind": "read"},
    {"title": "OkHttp Interceptor (source)", "url": "https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt", "kind": "read"}
   ]
  },
  {
   "h": "Where chains go wrong",
   "body": S4
  }
 ],
 "analogy": "A state machine is a board game's rule card: from this square, on this roll, you may move to that square, and nothing else. A chain of responsibility is the security line at an airport: ID check, bag scan, body scan, gate. Each station can wave you on or stop you, and the order matters, because there's no point scanning the bag of someone with no ticket. The analogy breaks on the way back. At an airport you never pass through security in reverse, but in a software chain the response travels back out through every station that let the request in, and each one can still change or log it.",
 "in_your_world": "Your payment and payout services already have state machines, often hidden in a status column and scattered `if (status == ...)` checks. Pull the rules into one pure transition function over sealed types, and the Oracle status column becomes a serialized state. A Temporal workflow is a durable state machine too: its history is the list of events, and replaying it rebuilds the state, which is why workflow code must be deterministic. On the chain side, Quarkus gives you JAX-RS `ContainerRequestFilter`s and CDI interceptors ordered by `@Priority`, and Kafka clients take a list of `ProducerInterceptor`s and `ConsumerInterceptor`s in config order. In each, write down which link owns auth, idempotency and retries, and in what order they run.",
 "mistake": "The most common mistake is a `default` (or `else`) branch on the outer switch over your own sealed state type. It is often added \"to be safe\" or to silence a warning while the type is young. From then on, a new state compiles without a word and quietly takes whatever the default does, usually \"reject every event\", so disputed payments get stuck and nobody notices until support does. Leave the default off the switch over states, and let each new state break the build at every place that needs a rule. Use `default` only on dimensions you don't expect to grow, such as the illegal events inside one state, or on open sets you don't control, such as vendor codes.",
 "compare": {
  "title": "Building the chain: an index walker and a fold",
  "java": {"title": "RealChain.java", "src": """// OkHttp's shape: an immutable chain object that knows its position
interface Chain { Response proceed(Request r); }
interface Interceptor { Response intercept(Request r, Chain next); }

record RealChain(List<Interceptor> interceptors, int index, Function<Request, Response> terminal) implements Chain {
    RealChain {
        interceptors = List.copyOf(interceptors);       // cheap after the first time: copyOf keeps an unmodifiable list
    }

    public Response proceed(Request r) {
        if (index == interceptors.size()) return terminal.apply(r);                       // past the last link
        return interceptors.get(index).intercept(r, new RealChain(interceptors, index + 1, terminal));
    }
}

Chain pipeline = new RealChain(List.of(logging, auth, idempotency), 0, handler);"""},
  "kotlin": {"title": "Chain.kt", "src": """// a function type replaces the Chain interface: the chain is just (HttpRequest) -> HttpResponse
fun interface Interceptor {
    fun intercept(r: HttpRequest, next: (HttpRequest) -> HttpResponse): HttpResponse
}

fun chain(interceptors: List<Interceptor>, terminal: (HttpRequest) -> HttpResponse): (HttpRequest) -> HttpResponse =
    interceptors.foldRight(terminal) { ic, next -> { r -> ic.intercept(r, next) } }   // wrap from the last to the first

val pipeline = chain(listOf(logging, auth, idempotency), handler)"""},
  "note": "Both call the interceptors in the same order and both are immutable. The Java record walks an index and creates a small chain object per step per request; that object is a natural place to carry more context, which is why OkHttp's real chain also exposes the call, its timeouts and the connection. The Kotlin fold builds the nested closures once, and `next` is a plain function, so no `Chain` interface is needed. Java can fold too, with a loop from the last interceptor to the first, as the lab's `FraudChain.build` does. What both languages make unnecessary is the GoF handler base class with a mutable `setNext()` link."
 },
 "worked": {
  "title": "Add chargebacks to the payment lifecycle",
  "steps": [
   {"say": "A captured payment can now be disputed. A dispute ends either won (back to `Captured`) or lost (a new terminal state, `ChargedBack`). Start with data only: the new states and events.",
    "code": """sealed interface PaymentState permits Created, Authorized, Captured, Refunded, Failed, Disputed, ChargedBack {}
record Disputed(String id, long amount, String caseId) implements PaymentState {}      // 1. new states
record ChargedBack(String id, long amount) implements PaymentState {}

sealed interface PaymentEvent permits Authorize, Capture, Refund, Decline, OpenDispute, WinDispute, LoseDispute {}
record OpenDispute(String caseId) implements PaymentEvent {}                            // 2. new events
record WinDispute() implements PaymentEvent {}
record LoseDispute() implements PaymentEvent {}""", "lang": "java",
    "alt_code": """sealed interface PaymentState {
    // ...the five existing states, plus:
    data class Disputed(val id: String, val amount: Long, val caseId: String) : PaymentState   // 1. new states
    data class ChargedBack(val id: String, val amount: Long) : PaymentState
}
sealed interface PaymentEvent {
    // ...the four existing events, plus:
    data class OpenDispute(val caseId: String) : PaymentEvent                              // 2. new events
    data object WinDispute : PaymentEvent
    data object LoseDispute : PaymentEvent
}""", "alt_lang": "kotlin"},
   {"say": "Compile before writing any rule. Every switch over `PaymentState` in the service fails. Count them: that is the size of the feature. Why do none of the inner event switches fail?",
    "code": """PaymentLifecycle.java:41: error: the switch expression does not cover all possible input values
StatusLabels.java:12: error: the switch expression does not cover all possible input values
LedgerMetrics.java:27: error: the switch expression does not cover all possible input values

(kotlinc: 'when' expression must be exhaustive. Add the 'is ChargedBack', 'is Disputed' branches or an 'else' branch.)""", "lang": "text"},
   {"say": "The inner switches have a `default`, so the new events are simply illegal in the old states until you say otherwise. Now write the rules. Note the choice in step 5: no refund while a dispute is open, because the money may be going back through the card scheme already.",
    "code": """case Captured(var id, var amt) -> switch (e) {
    case Refund(var r) when r > 0 && r <= amt -> new Refunded(id, r);
    case OpenDispute(var caseId) -> new Disputed(id, amt, caseId);       // 3. captured payments can be disputed
    default -> throw illegal(s, e);
};
case Disputed(var id, var amt, var caseId) -> switch (e) {
    case WinDispute() -> new Captured(id, amt);                          // 4. won: back to captured
    case LoseDispute() -> new ChargedBack(id, amt);                      // 5. lost: terminal; no refunds meanwhile
    default -> throw illegal(s, e);
};
case Refunded r -> throw illegal(s, e);
case Failed f -> throw illegal(s, e);
case ChargedBack cb -> throw illegal(s, e);                              // 6. terminal""", "lang": "java",
    "alt_code": """is PaymentState.Captured -> when (e) {
    is PaymentEvent.Refund if e.amount in 1..s.amount -> PaymentState.Refunded(s.id, e.amount)
    is PaymentEvent.OpenDispute -> PaymentState.Disputed(s.id, s.amount, e.caseId)   // 3. captured payments can be disputed
    else -> throw illegal(s, e)
}
is PaymentState.Disputed -> when (e) {
    PaymentEvent.WinDispute -> PaymentState.Captured(s.id, s.amount)                // 4. won: back to captured
    PaymentEvent.LoseDispute -> PaymentState.ChargedBack(s.id, s.amount)            // 5. lost: terminal; no refunds meanwhile
    else -> throw illegal(s, e)
}
is PaymentState.Refunded, is PaymentState.Failed, is PaymentState.ChargedBack -> throw illegal(s, e)   // 6. terminal""", "alt_lang": "kotlin"},
   {"say": "Fix the label and metrics switches the same way, then pin the new paths in tests. Because `transition` is pure, a whole dispute is one `replay` call with no PSP and no database.",
    "code": """@Test
void lostDisputeEndsChargedBack() {
    var events = List.<PaymentEvent>of(new Authorize("A-77", 5_000), new Capture(), new OpenDispute("CB-310"), new LoseDispute());
    assertThat(replay("p1", events)).isEqualTo(new ChargedBack("p1", 5_000));
}

@Test
void noRefundWhileDisputed() {
    assertThatThrownBy(() -> transition(new Disputed("p1", 5_000, "CB-310"), new Refund(100)))
            .hasMessage("Refund not allowed in Disputed");
}""", "lang": "java",
    "alt_code": """@Test
fun `a lost dispute ends charged back`() {
    val events = listOf(PaymentEvent.Authorize("A-77", 5_000), PaymentEvent.Capture, PaymentEvent.OpenDispute("CB-310"), PaymentEvent.LoseDispute)
    val end: PaymentState = events.fold(PaymentState.Created("p1"), ::transition)
    assertThat(end).isEqualTo(PaymentState.ChargedBack("p1", 5_000))
}

@Test
fun `no refund while disputed`() {
    assertThatThrownBy { transition(PaymentState.Disputed("p1", 5_000, "CB-310"), PaymentEvent.Refund(100)) }
        .isInstanceOf(IllegalStateException::class.java)
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A payment state machine and a fraud-check chain",
  "minutes": 14,
  "files": [f"{lab}/main/{J}/PaymentLifecycle.java", f"{lab}/main/{J}/FraudChain.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l09.*'",
  "steps": [
   "Read the table in the Javadoc of `PaymentLifecycle`, and the given `illegal` and `replay` methods. Run the tests: all ten fail.",
   "Write `transition` as a switch expression over the state with no `default`, and a switch over the event inside each state's case. Use record patterns and `when` guards for the amount rules.",
   "In `FraudChain`, write `build`: copy the list, start from `Chain next = terminal::apply`, and loop from the last check to the first, wrapping `next` each time.",
   "Write `amountLimit` and `countryMismatch` as one-line lambdas `(r, next) -> ...`.",
   "Run the tests until all ten pass. Then add a `Disputed` record to `PaymentState` (and to `permits`), build, read the error, and remove it."
  ],
  "hints": [
   "In a switch expression, `case Refunded r -> throw illegal(s, e);` is a complete case: a `throw` is allowed where a value is expected.",
   "A lambda can only capture effectively final variables, so copy the loop variable first: `Check check = copy.get(i); Chain rest = next; next = r -> check.check(r, rest);`.",
   "`case Captured(var id, var captured) -> switch (e) { case Refund(var r) when r > 0 && r <= captured -> ... }` takes the fields out and states the refund rule in one line."
  ],
  "done_when": "All ten tests in `StateChainTest` pass."
 },
 "drill": {
  "title": "Fold a chain from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `chain(interceptors, terminal)` that folds a list of interceptors into one function, where each interceptor gets the request and `next`. Then answer: for `[a, b, c]`, in what order do they run on the way in, and on the way out?",
  "answer": {"lang": "java", "src": """static Chain chain(List<Interceptor> interceptors, Chain terminal) {
    Chain next = terminal;
    for (int i = interceptors.size() - 1; i >= 0; i--) {   // wrap from the last to the first
        Interceptor ic = interceptors.get(i);
        Chain rest = next;
        next = r -> ic.intercept(r, rest);
    }
    return next;
}
// on the way in: a, b, c, then terminal; on the way out: c, b, a""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """fun chain(interceptors: List<Interceptor>, terminal: (HttpRequest) -> HttpResponse): (HttpRequest) -> HttpResponse =
    interceptors.foldRight(terminal) { ic, next -> { r -> ic.intercept(r, next) } }   // wrap from the last to the first

// on the way in: a, b, c, then terminal; on the way out: c, b, a"""}}
 },
 "recap": [
  "Model a lifecycle as sealed states, sealed events and one pure transition function. Record patterns and guards (`when`, or `if` in Kotlin 2.2+) state each rule in one line.",
  "No `default` on the switch over states: a new state then fails to compile at every place that needs a rule. A `default` on the inner event switch is fine, because most pairs are illegal.",
  "The compile-time check has a runtime remainder: `null` throws `NullPointerException`, and a separately compiled new subtype throws `MatchException` (Java) or `NoWhenBranchMatchedException` (Kotlin).",
  "A pure transition function makes history a fold: replaying the events rebuilds the state, with no mocks needed in tests.",
  "Chain of Responsibility: each link answers now or calls `next`. Code before `next` runs on the way in, code after it on the way out.",
  "Chains break on order, a forgotten `next`, a doubled `next` and exceptions. Pin the order in a test, and put after-logic in `finally`."
 ],
 "quiz": [
  {"q": "In `transition`, the outer `switch (s)` lists `Created`, `Authorized` and `Captured`, then ends with `default -> throw illegal(s, e)` instead of listing `Refunded` and `Failed`. Someone adds `Disputed`. What happens?",
   "options": ["The build fails at that switch", "It compiles, and every event on a disputed payment throws at runtime", "Disputed payments throw `NullPointerException`", "Disputed payments throw `MatchException`"],
   "answer": 1,
   "why": "The `default` covers every state not listed, including ones that don't exist yet, so the compiler has nothing to report. `Disputed` falls into the default and rejects every event, which looks like a stuck payment in production. `MatchException` is only for subtypes the compiler couldn't know about; this one it could have flagged."},
  {"q": "The rule is `case Refund(var r) when r > 0 && r <= captured -> new Refunded(id, r);` followed by `default -> throw illegal(s, e);`. A `Refund(6_000)` arrives for `Captured(\"p1\", 5_000)`. What happens?",
   "options": ["It returns `Refunded(\"p1\", 6_000)`", "It returns `Refunded(\"p1\", 5_000)`", "It throws `IllegalStateException(\"Refund not allowed in Captured\")`", "It doesn't compile, because the guard can be false"],
   "answer": 2,
   "why": "When a guard is false, that case doesn't match, and the switch tries the next case: here the `default`, which throws. Guards are part of the pattern, so an over-refund is just one more illegal move. Nothing clamps the amount."},
  {"q": "A chain is `[logging, idempotency, auth]`. A request with idempotency key K and no token arrives, then the client fixes its token and retries with the same key K. What does the retry get?",
   "options": ["200 charged", "401 no token", "500 server error", "409 duplicate"],
   "answer": 3,
   "why": "Idempotency runs before auth, so the first request records K and only then gets 401. The retry finds K already used and is stopped with 409, so the customer is never charged. With auth first, the rejected request never reaches the idempotency check, and the retry goes through."},
  {"q": "Someone adds a retry interceptor at the front of the chain that calls `next.proceed(r)` again when the response is a 5xx. What is the risk?",
   "options": ["Every later step runs again on each retry, including the fraud check and the charge", "Nothing: retries are always safe in a chain", "The retry can't reach the terminal step", "Only the logging step runs twice"],
   "answer": 0,
   "why": "`next` is the whole rest of the chain, so retrying it repeats every step after the retry interceptor, the charge included. If the PSP took the money and then timed out, the retry charges again (or, with an idempotency check in the chain, returns a confusing 409). Retry around the PSP client call, with an idempotency key."},
  {"q": "From *Strategy and Template Method*: a `PaymentState` and a `FeeStrategy` both hold behavior behind an interface. What actually differs?",
   "options": ["Only strategies can be lambdas", "The client chooses a strategy and it stays; a state machine chooses its own next state as events arrive", "States must be classes, strategies must be functions", "A strategy can't depend on data"],
   "answer": 1,
   "why": "Structurally they're the same: an object holds a value and behavior depends on it. The difference is control. You pick a fee strategy once per payment method and it doesn't change itself. A payment's state moves on its own, from `Authorized` to `Captured`, as the transition function processes events.",
   "from": "pat-07"}
 ],
 "flashcards": [
  {"front": "What replaces the GoF State pattern's class-per-state in Java 21 and Kotlin?", "back": "Sealed states and events as records or data classes, plus one pure `transition(state, event)` function with an exhaustive switch or `when`."},
  {"front": "Why leave `default` off the switch over a sealed state type?", "back": "So a new state fails to compile at every switch that needs a rule. A default would silently absorb it."},
  {"front": "When is `default` fine inside a state machine?", "back": "On the inner switch over events, where most (state, event) pairs are illegal. Never on the dimension you expect to grow."},
  {"front": "An exhaustive Java switch meets a sealed subtype compiled after it. What happens? And in Kotlin?", "back": "Java throws `MatchException`; Kotlin throws `NoWhenBranchMatchedException`. A null state throws `NullPointerException`."},
  {"front": "Why keep the transition function pure?", "back": "It's tested without mocks, and history becomes a fold: replaying events rebuilds the state. Side effects run outside it."},
  {"front": "In a chain of responsibility, what are a handler's two choices?", "back": "Answer now (return a response or verdict), or pass the request on by calling `next`."},
  {"front": "Interceptors `[a, b, c]`: order on the way in, and on the way out?", "back": "In: a, b, c, then the terminal step. Out: c, b, a."}
 ],
 "terms": [
  {"term": "State machine", "plain": "A set of states and the events that move between them; anything not listed is illegal."},
  {"term": "Transition function", "plain": "A pure function from the current state and an event to the next state."},
  {"term": "Guard", "plain": "An extra condition on a pattern case, such as `when amt > 0`; if false, the case doesn't match."},
  {"term": "Exhaustive switch", "plain": "A switch the compiler has checked covers every possible subtype or constant."},
  {"term": "Remainder", "plain": "The values an exhaustive switch can still meet at run time: null and subtypes compiled later."},
  {"term": "Chain of Responsibility", "plain": "A request passes along a list of handlers; each answers it or passes it on."},
  {"term": "Interceptor", "plain": "One link in a chain: it gets the request and the rest of the chain, and can act on the way in and out."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `transition` has no `default` on its outer switch but does have one on each inner switch, and what the compiler gives you when someone adds a `Disputed` state.",
  "answer": "The outer switch is over states, and states are what we expect to add: disputes, holds, partial captures. With no default, the compiler knows the switch must cover every permitted state, so adding `Disputed` makes every switch over `PaymentState` in the code fail to compile. Those errors are the list of places that need a decision, and the feature is finished when the build is green. The inner switches are over the events one state accepts. Most events are illegal in most states, and new events usually only matter in one or two states, so a `default` that throws \"not allowed\" is the honest rule there. Putting a default on the outer switch would swallow the new state silently, and disputed payments would just reject every event at runtime."
 },
 "deeper": {
  "minutes": 10,
  "body": """Pattern matching for `switch` (JEP 441) and record patterns (JEP 440) both became final in JDK 21, so everything in this lesson compiles with `--release 21` and no preview flags. In Kotlin, sealed subclasses must live in the same package and module as their parent, and guards in `when` with a subject became stable in 2.2.0.

Keeping the transition pure doesn't mean the machine does nothing. A common shape returns the next state together with a list of effects to run, such as \"call the PSP\", \"post to the ledger\" or \"send a receipt\", as sealed records. A thin outer layer executes them and feeds the results back in as events. Tests then assert on the returned effects, not on mocks. Temporal workflows work in a similar spirit: workflow code decides, activities do the I/O, and the history of events lets Temporal replay the workflow to rebuild its state.

Event sourcing takes replay to its end: store the events, not the state, and compute the state as a fold. Long histories get slow to replay, so systems store a snapshot every few hundred events and replay only what came after. That snapshot is a memento, from lesson 10 of this track, *Visitor, Iterator, Mediator and Memento*.

Chain of Responsibility also shows up per method, not only per request. A CDI interceptor's `@AroundInvoke` method receives an `InvocationContext` and calls `proceed()` to continue to the next interceptor or the bean itself. Transactions, metrics and fault-tolerance annotations in Quarkus are built this way, which is why the proxy rules from *Decorator and Proxy* still apply to them."""
 },
 "sources": [
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "JEP 441: Pattern matching for switch", "url": "https://openjdk.org/jeps/441"},
  {"title": "Exhaustiveness, unconditionality and remainder (Goetz and Bierman)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md"},
  {"title": "Jakarta Servlet FilterChain (source)", "url": "https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/FilterChain.java"},
  {"title": "OkHttp Interceptor (source)", "url": "https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt"}
 ]
}

out = ROOT / "content/lessons/pat-09.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
