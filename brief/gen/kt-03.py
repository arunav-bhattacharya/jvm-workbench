import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l03"
DK = "kotlin/workbench/kotlin/l03/demo"
DJ = "java/workbench/kotlin/l03/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l03.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="A delegated property compiles to a hidden delegate field, a static array of KProperty objects, and accessors that call getValue and setValue on the delegate">'
    '<rect class="box-a" x="20" y="96" width="200" height="64" rx="8"/>'
    '<text class="t t-code" x="120" y="122" text-anchor="middle">var status: String</text>'
    '<text class="t-s t-code" x="120" y="144" text-anchor="middle">by Audited("NEW")</text>'
    '<line class="ln-a" x1="226" y1="128" x2="292" y2="128" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="259" y="116" text-anchor="middle">javac sees</text>'
    '<rect class="box" x="300" y="20" width="360" height="222" rx="8"/>'
    '<text class="t t-code" x="480" y="44" text-anchor="middle">class Order</text>'
    '<rect class="box-dim" x="316" y="58" width="328" height="34" rx="8"/>'
    '<text class="t-s t-code" x="480" y="80" text-anchor="middle">static KProperty[] $$delegatedProperties</text>'
    '<rect class="box-b" x="316" y="100" width="328" height="34" rx="8"/>'
    '<text class="t-s t-code" x="480" y="122" text-anchor="middle">private final Audited status$delegate</text>'
    '<rect class="box" x="316" y="142" width="328" height="34" rx="8"/>'
    '<text class="t-s t-code" x="480" y="164" text-anchor="middle">getStatus(): d.getValue(this, p[0])</text>'
    '<rect class="box" x="316" y="184" width="328" height="34" rx="8"/>'
    '<text class="t-s t-code" x="480" y="206" text-anchor="middle">setStatus(v): d.setValue(this, p[0], v)</text>'
    '<text class="t-s t-m" x="120" y="196" text-anchor="middle">one delegate object per</text>'
    '<text class="t-s t-m" x="120" y="214" text-anchor="middle">property, per instance</text>'
    '</svg>'
)

L = {
 "id": "kt-03",
 "title": "Delegation: class delegation and delegated properties",
 "minutes": 35,
 "goal": "By the end you can predict what `by` forwards and to which object, read the fields the compiler generates for a delegated property, say what `by lazy` costs, and write your own delegate with `provideDelegate` validation.",
 "warmup": {
  "q": "`class ConfigurableFees(var policy: FeePolicy) : FeePolicy by policy`. You build it with `FlatFee(25)`, then set `fees.policy = FlatFee(99)`. What does `fees.feeMinor(10_000)` return?",
  "options": ["99, because `by policy` forwards to the property", "25, because the delegate was captured when the object was built", "It doesn't compile: a `var` can't be a delegate", "It throws, because the delegate changed under it"],
  "answer": 1,
  "why": "The compiler copies the constructor argument into a hidden `private final FeePolicy $$delegate_0` field, and the generated `feeMinor` calls that field. Assigning `policy` changes the property only. It compiles without a warning, which is why the first option catches people."
 },
 "sections": [
  {
   "h": "Class delegation forwards to the object you passed in, once",
   "body": "Lesson 5 of the patterns track showed what `by` writes for you: every method of the interface, forwarded to the object you named, except the ones you override. It also showed the trap: `putAll` goes straight to the inner map and never sees your `put` override. Two more details matter once you put `by` into real classes.\n\nThe first is that the delegate is captured once. `class ConfigurableFees(var policy: FeePolicy) : FeePolicy by policy` looks like it forwards to the `policy` property. `javap` shows two fields instead:\n\n```text\nprivate final FeePolicy $$delegate_0;   // set from the constructor argument, never changed\nprivate FeePolicy policy;               // the property you can reassign\n```\n\nThe generated `feeMinor` calls `$$delegate_0`. Assign a new policy and the property changes, but every call still goes to the old object: the demo prints `after swap, policy = FlatFee(99), fee: 25`. A hand-written Java decorator reads its field on every call, so swapping works there:\n\n```java\nfinal class ConfigurableFeesJava implements FeePolicy {\n    private FeePolicy policy;\n    ConfigurableFeesJava(FeePolicy policy) { this.policy = policy; }\n    void setPolicy(FeePolicy policy) { this.policy = policy; }\n\n    @Override public long feeMinor(long amountMinor) {\n        return policy.feeMinor(amountMinor);       // the current field, on every call\n    }\n}\n```\n\n```kotlin\nclass ConfigurableFees(var policy: FeePolicy) : FeePolicy by policy   // forwards to the FIRST policy\n\nval fees = ConfigurableFees(FlatFee(25))\nfees.policy = FlatFee(99)\nfees.feeMinor(10_000)   // 25: $$delegate_0 still holds FlatFee(25)\n```\n\nIf the target has to change at run time, write the forwarding yourself. Otherwise make the constructor parameter a plain parameter or a `val`, so nobody expects it to move.\n\nThe second detail: `equals`, `hashCode` and `toString` are not forwarded. They come from `Any`, not from the interface. A `Tags` class that delegates `MutableSet<String>` prints as `Tags@2752f6e2`, and two `Tags` with the same elements are not equal. That breaks the `Set` contract, which says two sets with the same elements are equal, and a `HashSet<Tags>` will happily keep both. Override the three and forward them to the inner set when the wrapper should behave like what it wraps.\n\nWith those two rules in mind, `by` is still the best tool for one job: wrapping a wide Java interface to change one or two methods. A `DataSource` that counts borrowed connections, a Kafka `Producer` that adds a trace header to every record: you write the methods you change, and the compiler writes the other twenty, with no chance of forgetting one when the interface grows a new method in the next library version.",
   "try": {
    "title": "Swap a delegate and watch nothing happen",
    "minutes": 4,
    "steps": [
     "Run `ClassDelegationDemo`. Before you read the second line, predict the fee after the swap.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l03.demo.ConfigurableFees` from `labs/` and find both fields.",
     "Run `ClassDelegationDemoJava`, which swaps a hand-written Java decorator and then the Kotlin class from Java.",
     "In `Tags`, add `override fun equals(other: Any?) = other is Set<*> && inner == other` and `override fun hashCode() = inner.hashCode()`. Run again."
    ],
    "code": demo("ClassDelegationDemo"),
    "expect": "Kotlin prints `fee: 25`, then `after swap, policy = FlatFee(99), fee: 25`: the property moved, the calls didn't. `javap` lists `private final ...FeePolicy $$delegate_0` and `private ...FeePolicy policy`. The Java decorator prints 99 after its swap, and the Kotlin class still prints 25 when Java swaps it. `a == b` is `false` until you add `equals` and `hashCode`, then `true`."
   },
   "refs": [{"title": "Delegation (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegation.html", "kind": "docs"}]
  },
  {
   "h": "A delegated property is a hidden field and two calls",
   "body": "Property delegation shares the keyword and almost nothing else. Start without it. Say every change to an order's status must be logged, and you want the logging written once, in a small helper class you can reuse for any audited property. By hand, the property forwards its getter and setter to the helper:\n\n```java\nfinal class OrderJava {\n    private final Box<String> status = new Box<>(\"NEW\");     // the helper holds the value\n    String getStatus() { return status.get(); }\n    void setStatus(String s) { status.set(\"status\", s); }    // and logs every change\n}\n```\n\n```kotlin\nclass Order {\n    private val statusBox = Audited(\"NEW\")                   // the helper holds the value\n    var status: String\n        get() = statusBox.getValue(this, ::status)\n        set(value) = statusBox.setValue(this, ::status, value)   // and logs every change\n}\n```\n\n`::status` is a reference to the property itself, a `KProperty`, which knows its name, so the helper can log `status` without a string literal that could drift. That forwarding is all `by` does. The helper object is called the **delegate**, and it only needs two functions with fixed names, and `by` writes the getter and setter for you:\n\n```java\n// Java has no `by`: the helper is an ordinary class, and you write the forwarding above yourself\nfinal class Box<T> {\n    private T value;\n    Box(T value) { this.value = value; }\n    T get() { return value; }\n    void set(String name, T value) {\n        System.out.println(\"  \" + name + \": \" + this.value + \" -> \" + value);\n        this.value = value;\n    }\n}\n```\n\n```kotlin\nclass Audited<T>(private var value: T) : ReadWriteProperty<Any?, T> {\n    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value\n\n    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {\n        println(\"  ${property.name}: ${this.value} -> $value\")\n        this.value = value\n    }\n}\n\nclass Order {\n    var status: String by Audited(\"NEW\")      // the same forwarding, written by the compiler\n}\n```\n\n`getValue` receives the owning object (`thisRef`) and a `KProperty` that describes the property, including its name. A `val` needs only `getValue`. You can write them as `operator fun` members or extensions on any class, or implement `ReadOnlyProperty` or `ReadWriteProperty` as here.\n\nThe compiler's version matches your hand-written one with one change, shown in the figure. For each delegated property it adds a hidden field, `status$delegate`, typed as whatever the expression after `by` returns. Instead of a fresh `::status` on every call, it builds one static array per class, `$$delegatedProperties`, with a `KProperty` object per property, filled once in the static initializer. Then `getStatus()` loads `status$delegate`, loads `$$delegatedProperties[0]`, calls `getValue`, and casts the result to `String`.\n\nJava sees none of this. It sees `getStatus()` and `setStatus(String)`, ordinary methods; the delegate field is private and the array is package-private. That suits frameworks that work through getters and setters. It's also a warning: a setter that logs, validates or audits looks exactly like a plain setter from the outside.\n\nA few kinds of delegate get no `$delegate` field: delegating to another property (`by this::amountMinor`), to a named object, to `this`, or to a constant. The docs list the cases. Everything else costs one extra object per delegated property, per instance.\n\nThe operators don't have to live in the delegate's class. They can be extension functions, and that's how `by settings` works on a plain `Map` in the last section: the standard library declares `getValue` as an inline extension operator on `Map`, which looks up the key `property.name`. You can do the same for a type you don't own. An `operator fun Headers.getValue(thisRef: Any?, property: KProperty<*>): String` would let a class write `val traceId: String by kafkaHeaders`.",
   "figure": {"svg": FIG, "caption": "What the compiler writes for one delegated property: a field for the delegate, a shared KProperty array, and accessors that call the delegate."},
   "try": {
    "title": "Find the generated field and array",
    "minutes": 4,
    "steps": [
     "Run `PropertyDelegateDemo`, then `PropertyDelegateDemoJava`, which calls the same `Order` through `setStatus` and lists its fields by reflection.",
     "From `labs/`, run `javap -c -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l03.demo.Order` and read `getStatus`.",
     "Add `var note: String? by Audited(null)` to `Order` and set it in `main`. Predict the new fields before you run."
    ],
    "code": demo("PropertyDelegateDemo"),
    "expect": "Both print the two changes, then the fields: `KProperty[] $$delegatedProperties`, `Audited status$delegate` and `Audited amountMinor$delegate`. `getStatus` is `getfield status$delegate`, `getstatic $$delegatedProperties`, `iconst_0`, `aaload`, `invokevirtual Audited.getValue`, `checkcast String`. Adding `note` adds a `note$delegate` field and a third array entry, not a second array."
   },
   "refs": [{"title": "Delegated properties (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html", "kind": "docs"}]
  },
  {
   "h": "What by lazy costs: an object per instance and a call per read",
   "body": "`by lazy` is the delegate you use most, and the memory model track already took it apart: it is double-checked locking, `SYNCHRONIZED` by default, with `PUBLICATION` and `NONE` as the other modes (lesson 5 of that track). This section is about the bill.\n\n```java\n// Java's per-instance lazy field: volatile double-checked locking, by hand\nprivate volatile Double eurUsd;\n\ndouble eurUsd() {\n    Double v = eurUsd;\n    if (v == null) {\n        synchronized (this) {\n            v = eurUsd;\n            if (v == null) eurUsd = v = rates.fetch(\"EURUSD\");\n        }\n    }\n    return v;\n}\n```\n\n```kotlin\nclass FxQuote(private val rates: RateService) {\n    val eurUsd: Double by lazy { rates.fetch(\"EURUSD\") }    // SYNCHRONIZED\n}\n```\n\nEach `FxQuote` gets a `private final kotlin.Lazy eurUsd$delegate` field. The constructor fills it with a new `SynchronizedLazyImpl` (fields `initializer`, `_value` and `lock`), and the initializer lambda is a second object. Every read calls `Lazy.getValue()` through an interface, and for a `Double` it then unboxes with `checkcast Number` and `doubleValue`. There's no `$$delegatedProperties` array, because `lazy` never looks at the property.\n\nFor one configuration object, none of that matters. For a class you create per payment, per Kafka record or per database row, it's two extra objects every time, for a value you may never read. Use `lazy` on long-lived objects: singletons, `@ApplicationScoped` beans, caches. For short-lived ones, compute the value in the constructor or make it a function.\n\nWhen only one thread can ever touch the object, `lazy(LazyThreadSafetyMode.NONE)` drops the lock and the class becomes `UnsafeLazyImpl`. The docs say it \"doesn't incur any thread-safety guarantees and related overhead\". Think of a parser or a report builder that lives inside one function call. Don't use it on anything a CDI container shares: an `@ApplicationScoped` bean is read from many request threads at once, and `NONE` gives you no guarantee that they all see one value.\n\nOne behavior is easy to miss. `lazy` doesn't cache an exception. In the demo the first read throws `rate service timed out`, and the second read runs the initializer again and succeeds. For a remote call that's usually what you want.",
   "try": {
    "title": "Count the initializer runs",
    "minutes": 3,
    "steps": [
     "Run `LazyDemo`. Before you do, predict how many times the initializer runs over three reads when the first one throws.",
     "Run `LazyDemoJava`, which does the same with hand-written double-checked locking and then reads the Kotlin class from Java.",
     "Run `javap -c -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l03.demo.FxQuote` and read `getEurUsd`."
    ],
    "code": demo("LazyDemo"),
    "expect": "The three modes map to `kotlin.SynchronizedLazyImpl`, `kotlin.SafePublicationLazyImpl` and `kotlin.UnsafeLazyImpl`. The first read fails, the second succeeds, and the initializer ran 2 times, not 3: once the value is stored, reads stop calling it. The only field is `kotlin.Lazy eurUsd$delegate`, and `getEurUsd` is `getfield`, `invokeinterface Lazy.getValue`, `checkcast Number`, `doubleValue`. The Java version behaves the same."
   },
   "refs": [{"title": "Delegated properties: lazy (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html", "kind": "docs"}]
  },
  {
   "h": "The standard delegates, and provideDelegate for early checks",
   "body": "The standard library ships the delegates you'd otherwise write by hand. `Delegates.observable(initial) { property, old, new -> }` calls you after every assignment. `Delegates.vetoable(initial) { property, old, new -> Boolean }` calls you before it, and returning `false` keeps the old value. And a `val` can read from a `Map`: `val host: String by settings` looks up the key `\"host\"`. A `var` does the same with a `MutableMap`. `Delegates.notNull<Int>()` covers what `lateinit` can't, a primitive: reading it before the first assignment throws `Property size should be initialized before get.`\n\n```java\nvoid setOwner(String owner) {                          // observable, by hand\n    String old = this.owner;\n    this.owner = owner;\n    System.out.println(\"owner: \" + old + \" -> \" + owner);\n}\n\nvoid setLimit(int limit) {                             // vetoable, by hand\n    if (limit <= 100) this.limit = limit;\n}\n\nint port() { return (Integer) settings.get(\"port\"); }  // map-backed, by hand\n```\n\n```kotlin\nvar owner: String by Delegates.observable(\"<none>\") { property, old, new ->\n    println(\"${property.name}: $old -> $new\")\n}\nvar limit: Int by Delegates.vetoable(100) { _, _, new -> new <= 100 }\n\nval port: Int by settings                              // settings[\"port\"], cast to Int\n```\n\nThe demo prints `owner: <none> -> alice`, `owner: alice -> bob`, `limit after veto: 100` and `limit after ok: 50`. A map-backed property fails only when you read it: a missing key throws `java.util.NoSuchElementException: Key port is missing in the map.` That's late. For configuration you'd rather fail when the object is built, and that's what `provideDelegate` is for.\n\nIf the object after `by` has an `operator fun provideDelegate(thisRef, property)`, the compiler calls it once per property, while the owning object is being constructed, and keeps what it returns as the real delegate. The docs describe it as the way to get \"the necessary validation right away\". `PropertyDelegateProvider { thisRef, property -> ... }` creates one without a new class. In the demo, `binding issuerUrl` prints during `Settings()`, before anyone reads the property. The lab uses the same trick to register every audited property up front.",
   "try": {
    "title": "Watch the standard delegates fire",
    "minutes": 4,
    "steps": [
     "Run `StdDelegatesDemo` (or its Java twin). Predict the order of `building Settings...`, `binding issuerUrl` and `built; ...` before you look.",
     "Change the veto to `new <= 40` and run. Predict both `limit` lines first.",
     "Remove `\"host\" to \"issuer.example\"` from the map. Predict which line fails, and when."
    ],
    "code": demo("StdDelegatesDemo"),
    "expect": "`building Settings...` comes first, then `binding issuerUrl` while the constructor runs, then `built; issuerUrl = value of issuerUrl`. With `new <= 40` both assignments are vetoed, so both lines print 100: the handler checks assignments, never the initial value. Without `host`, building `IssuerConfig` still works and the program fails on the `config.host` read with `Key host is missing in the map.`"
   }
  }
 ],
 "analogy": "A delegated property is a flat with a building manager. You own the flat, but every request to get in or change something goes through the manager, who can keep a log, refuse a change, or fetch the keys only on the first visit. Visitors from outside (Java callers) see an ordinary front door, a getter and a setter. The analogy breaks at class delegation: there the manager is fixed on the day the building opens, and changing the name on the mailbox (the `var`) doesn't change who answers.",
 "in_your_world": "Audit trails are the obvious fit in payments: a `PaymentDraft` whose `status` and `amountMinor` record every change for the compliance log, written once as a delegate instead of in every setter. Quarkus configuration usually arrives through `@ConfigMapping` interfaces, but code that reads a parsed `Map` (a merchant's routing rules from a JSON column, Kafka headers) can use map-backed properties, with `provideDelegate` to check the required keys when the object is built rather than on the first payment that needs them. And be careful with `by` on CDI beans: a bean that delegates an interface to a constructor argument keeps that argument forever. That's fine for an injected client, and wrong for anything you meant to swap at run time, such as a fee policy behind a feature flag.",
 "mistake": "Swapping the target of class delegation at run time. `class Router(var gateway: Gateway) : Gateway by gateway` invites a feature flag to set `router.gateway = newGateway`:\n\n```java\n// the Java decorator people have in mind: it reads the field on every call\n@Override public String authorize(Payment p) { return gateway.authorize(p); }\n```\n\n```kotlin\nclass Router(var gateway: Gateway) : Gateway by gateway\n\nrouter.gateway = newGateway     // the property changes; authorize() still calls the old gateway\n```\n\nThe assignment works, the property changes, and every call still goes to the gateway passed to the constructor, because the compiler copied it into a hidden final `$$delegate_0` field. Nothing fails; the traffic simply never moves. If the target must change, write the forwarding methods yourself so they read the property each time, or forward to an `AtomicReference<Gateway>`.",
 "compare": {
  "title": "An audited field: Java setters vs a Kotlin delegate",
  "java": {"title": "PaymentDraft.java", "src": "public final class PaymentDraft {\n    private final ChangeLog log;\n    private String status = \"NEW\";\n    private long amountMinor = 0;\n\n    public PaymentDraft(ChangeLog log) { this.log = log; }\n\n    public String getStatus() { return status; }\n    public void setStatus(String s) {\n        if (!s.equals(status)) log.record(\"status\", status, s);   // repeated in every setter\n        status = s;\n    }\n\n    public long getAmountMinor() { return amountMinor; }\n    public void setAmountMinor(long a) {\n        if (a != amountMinor) log.record(\"amountMinor\", amountMinor, a);\n        amountMinor = a;\n    }\n}"},
  "kotlin": {"title": "PaymentDraft.kt", "src": "class Recorded<T>(private var value: T, private val log: ChangeLog) : ReadWriteProperty<Any?, T> {\n    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value\n    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {\n        if (value != this.value) log.changes += Change(property.name, this.value, value)\n        this.value = value\n    }\n}\n\nclass PaymentDraft(val log: ChangeLog) {\n    var status: String by Recorded(\"NEW\", log)        // the audit is written once, in Recorded\n    var amountMinor: Long by Recorded(0L, log)\n}"},
  "note": "In Java the audit lives in every setter, and a new field without it is a silent gap that only review can catch. In Kotlin it's written once, in the delegate, and each property opts in with `by`. The property name comes from the `KProperty` the compiler passes in, so it can't drift from the field name the way a string literal can. The run-time price is one delegate object per property per instance, plus one static `KProperty` array per class. Java code calling the Kotlin class can't tell the two apart: it sees `getStatus` and `setStatus` either way."
 },
 "worked": {
  "title": "A config object that fails at startup, not on the first payment",
  "steps": [
   {"say": "Start with a map-backed config. It reads nicely, but a missing key is found only when someone reads the property, which may be the first payment routed to that acquirer at 2 a.m.",
    "code": "final class RoutingConfig {\n    private final Map<String, Object> settings;\n    RoutingConfig(Map<String, Object> settings) { this.settings = settings; }\n\n    String acquirer() { return (String) settings.get(\"acquirer\"); }   // null if missing\n    long timeoutMs() { return (Long) settings.get(\"timeoutMs\"); }     // NullPointerException if missing\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class RoutingConfig(settings: Map<String, Any?>) {\n    val acquirer: String by settings      // NoSuchElementException, but only when read\n    val timeoutMs: Long by settings\n}"},
   {"say": "Write a provider. `provideDelegate` runs once per property while the object is built, so it can check the key right away and hand back a delegate that only returns the value it read.",
    "code": "fun <T> Map<String, Any?>.required(): PropertyDelegateProvider<Any?, ReadOnlyProperty<Any?, T>> =\n    PropertyDelegateProvider { _, property ->\n        // 1. check the key while the owning object is constructed\n        require(property.name in this) { \"missing config key '${property.name}'\" }\n        @Suppress(\"UNCHECKED_CAST\")\n        val value = this[property.name] as T\n        // 2. the real delegate just returns what was read\n        ReadOnlyProperty { _, _ -> value }\n    }\n\nclass RoutingConfig(settings: Map<String, Any?>) {\n    val acquirer: String by settings.required()\n    val timeoutMs: Long by settings.required()\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java does the same check in the constructor, one line per key\nRoutingConfig(Map<String, Object> settings) {\n    this.acquirer = (String) require(settings, \"acquirer\");\n    this.timeoutMs = (Long) require(settings, \"timeoutMs\");\n}\n\nprivate static Object require(Map<String, Object> m, String key) {\n    if (!m.containsKey(key)) throw new IllegalArgumentException(\"missing config key '\" + key + \"'\");\n    return m.get(key);\n}"},
   {"say": "Build one with a key missing. It fails in the constructor, with the property's name in the message, because the name came from the `KProperty` the compiler passed in.",
    "code": "RoutingConfig(mapOf(\"acquirer\" to \"acq-a\", \"timeoutMs\" to 2_000L))   // fine\nRoutingConfig(mapOf(\"acquirer\" to \"acq-a\"))\n// java.lang.IllegalArgumentException: missing config key 'timeoutMs'", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "new RoutingConfig(Map.of(\"acquirer\", \"acq-a\", \"timeoutMs\", 2_000L));   // fine\nnew RoutingConfig(Map.of(\"acquirer\", \"acq-a\"));\n// java.lang.IllegalArgumentException: missing config key 'timeoutMs'"},
   {"say": "The cast is still unchecked: a `\"timeoutMs\" to \"2000\"` entry passes the check and fails later with a `ClassCastException` on the first read. If that matters, pass the expected class into `required` and check it with `isInstance`, the class-token trick from the generics track.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "An audited property delegate",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Recorded.kt", f"{lab}/main/{P}/PaymentDraft.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l03.*'",
  "steps": [
   "Run the tests. All six fail, most with `NotImplementedError` thrown while a `PaymentDraft` is being built. That's `provideDelegate` at work already.",
   "In `Recorded.kt`, write `getValue` and `setValue` (TODOs 1 and 2). Record a `Change` only when the value really changes.",
   "Write `ChangeLog.recorded` (TODO 3): return a `PropertyDelegateProvider` that checks and registers `property.name`, then creates the `Recorded`.",
   "In `PaymentDraft.kt`, make `currency` a vetoable delegate (TODO 4), and delegate both `MerchantConfig` properties to the map (TODO 5).",
   "Run the tests until all six pass, including `DraftFromJavaTest`, which only sees `setStatus` and `getLog`. Then run `javap -p -cp kotlin/build/classes/kotlin/main workbench.kotlin.l03.PaymentDraft` and match each field to a property."
  ],
  "hints": [
   "In `setValue`, the parameter `value` shadows the field. Compare with `if (value != this.value)`, record `Change(property.name, this.value, value)`, then assign `this.value = value`.",
   "`PropertyDelegateProvider { _, property -> check(property.name !in tracked) { \"...\" }; tracked += property.name; Recorded(initial, this) }`. Inside the lambda, `this` is still the `ChangeLog` receiver.",
   "`var currency: String by Delegates.vetoable(\"EUR\") { _, _, new -> new.matches(Regex(\"[A-Z]{3}\")) }`, with `import kotlin.properties.Delegates`.",
   "`val name: String by settings` needs no import. Delete the `get() = TODO(...)` and write `by settings` in its place."
  ],
  "done_when": "All six tests in `DelegationTest` and `DraftFromJavaTest` pass."
 },
 "drill": {
  "title": "Write a clamping delegate from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `class Clamped(min: Int, max: Int, initial: Int)` as a `ReadWriteProperty<Any?, Int>` that keeps every assigned value inside `min..max`, and use it as `var discountBps: Int by Clamped(0, 10_000, initial = 0)`. Then write the Java setter that does the same. What does `discountBps = 12_000` leave behind?",
  "answer": {"lang": "kotlin", "src": "class Clamped(private val min: Int, private val max: Int, initial: Int) : ReadWriteProperty<Any?, Int> {\n    private var value = initial.coerceIn(min, max)\n\n    override fun getValue(thisRef: Any?, property: KProperty<*>): Int = value\n\n    override fun setValue(thisRef: Any?, property: KProperty<*>, value: Int) {\n        this.value = value.coerceIn(min, max)\n    }\n}\n\nclass Discount {\n    var discountBps: Int by Clamped(0, 10_000, initial = 0)   // 12_000 is stored as 10_000\n}",
             "alt": {"lang": "java", "title": "Discount.java", "src": "final class Discount {\n    private int discountBps = 0;\n\n    int getDiscountBps() { return discountBps; }\n\n    void setDiscountBps(int bps) {\n        discountBps = Math.max(0, Math.min(10_000, bps));     // 12_000 is stored as 10_000\n    }\n}"}}
 },
 "recap": [
  "Class delegation (`: Iface by x`) forwards every interface method you don't override to `x`, captured once into a hidden final `$$delegate_0` field. Reassigning a `var` doesn't move it.",
  "`equals`, `hashCode` and `toString` are not forwarded, and the delegate never calls back into your overrides.",
  "A delegated property compiles to a `prop$delegate` field, a static `$$delegatedProperties` array of `KProperty` objects, and accessors that call `getValue` and `setValue`. Java sees plain getters and setters.",
  "`by lazy` costs a `Lazy` object and an initializer lambda per instance, plus an interface call on every read. It doesn't cache exceptions. Use `NONE` for single-threaded objects.",
  "`observable` runs after an assignment, `vetoable` before it, and `by map` reads a key named after the property when you read it.",
  "`provideDelegate` runs once per property while the object is built: the place for early validation and registration."
 ],
 "quiz": [
  {"q": "What does this print?\n\n```kotlin\nclass Fees(var policy: FeePolicy) : FeePolicy by policy\n\nval fees = Fees(FlatFee(25))\nfees.policy = FlatFee(99)\nprintln(fees.feeMinor(10_000))\n```",
   "options": ["`25`", "`99`", "An `IllegalStateException`", "`0`"],
   "answer": 0, "why": "`by policy` reads the constructor argument once and stores it in `$$delegate_0`. The generated `feeMinor` calls that field, so the swap changes only the property. 99 is what a hand-written decorator that reads its field each call would print."},
  {"q": "Which fields does `class Order { var status: String by Audited(\"NEW\") }` have in the bytecode?",
   "options": ["`private String status`", "`private final Audited status$delegate`, plus a static `KProperty[] $$delegatedProperties`", "One static `Audited` shared by every `Order`", "None: the delegate is inlined into `getStatus`"],
   "answer": 1, "why": "Each delegated property gets a hidden field holding its delegate, typed as the delegate expression, and each class gets one static array of `KProperty` objects that the accessors pass to `getValue` and `setValue`. Nothing is shared between instances, and nothing is inlined."},
  {"q": "An `AuthorizationEvent` is created 2 million times a minute in a Kafka consumer. It has `val summary: String by lazy { describe(this) }`, which is read for about 1% of events. What's the best change?",
   "options": ["Keep it: `lazy` costs nothing until it's read", "Switch to `lazy(LazyThreadSafetyMode.PUBLICATION)`", "Mark the property `@Volatile`", "Make it a function or a getter, `val summary get() = describe(this)`, computed on demand"],
   "answer": 3, "why": "`lazy` allocates the `Lazy` object and the initializer lambda in the constructor, for every event, read or not. A getter without a backing field costs nothing until called. Changing the mode keeps both allocations; it only changes the locking."},
  {"q": "`class IssuerConfig(settings: Map<String, Any?>) { val port: Int by settings }`, and `settings` has no `\"port\"` key. When does it fail?",
   "options": ["When `IssuerConfig` is constructed", "At compile time", "Never: `port` reads as 0", "When `port` is read: `NoSuchElementException: Key port is missing in the map.`"],
   "answer": 3, "why": "A map-backed property is a lookup in its getter. Building the object only stores the map. To fail at construction, check the key in a `provideDelegate`, which runs while the object is built."},
  {"q": "From the memory model track: two threads read `val rules by lazy { download() }` for the first time at the same moment. What happens?",
   "options": ["`download()` may run twice, and each thread keeps its own result", "`download()` runs once; the other thread waits and sees the same value", "Nothing is guaranteed unless the property is `@Volatile`", "The second thread gets `ConcurrentModificationException`"],
   "answer": 1, "why": "The default mode is `SYNCHRONIZED`: double-checked locking with a lock, so one thread runs the initializer and the other waits for it. The first option describes `PUBLICATION`, where several threads may run it but all see the first stored value.",
   "from": "jmm-05"}
 ],
 "flashcards": [
  {"front": "`class Fees(var policy: FeePolicy) : FeePolicy by policy`. After `fees.policy = other`, which object gets the calls?", "back": "The original one. The compiler copied it into a hidden final field, `$$delegate_0`, at construction."},
  {"front": "Does class delegation forward `equals`, `hashCode` and `toString`?", "back": "No. They come from `Any`, not from the interface. Override them yourself if the wrapper should behave like what it wraps."},
  {"front": "Which functions does a delegate for a `var` need?", "back": "`getValue(thisRef, property: KProperty<*>)` and `setValue(thisRef, property, value)`, as operators or via `ReadWriteProperty`. A `val` needs only `getValue`."},
  {"front": "What does the compiler generate for `var status by Audited(\"NEW\")`?", "back": "A `status$delegate` field holding the delegate, a static `$$delegatedProperties` array of `KProperty`, and accessors that call `getValue`/`setValue` on the delegate."},
  {"front": "What does `by lazy` cost per instance?", "back": "A `Lazy` object (`SynchronizedLazyImpl` by default) and an initializer lambda, created in the constructor, plus an interface call, and unboxing for primitives, on every read."},
  {"front": "`observable` vs `vetoable`: when does each handler run?", "back": "`observable` runs after the assignment. `vetoable` runs before it, and returning `false` keeps the old value."},
  {"front": "When does `provideDelegate` run?", "back": "Once per property, while the owning object is being constructed, before any read. That makes it the place for early validation."}
 ],
 "terms": [
  {"term": "Class delegation", "plain": "`class A(x: I) : I by x`: the compiler writes every method of `I` as a call on `x`, except the ones you override."},
  {"term": "Delegated property", "plain": "A property whose get and set are handed to another object with `by`."},
  {"term": "$delegate field", "plain": "The hidden field, such as `status$delegate`, that holds a property's delegate."},
  {"term": "KProperty", "plain": "A run-time description of a property (its name, its type), passed to `getValue` and `setValue`."},
  {"term": "Lazy", "plain": "The standard delegate that computes a value on first read and keeps it. Three thread-safety modes."},
  {"term": "provideDelegate", "plain": "An operator the compiler calls once per property at construction, to create or check the real delegate."},
  {"term": "Map-backed property", "plain": "`val host: String by settings`: reads `settings[\"host\"]` each time the property is read."}
 ],
 "explain_back": {
  "prompt": "A teammate asks what the compiler actually generates for `var status: String by log.recorded(\"NEW\")` in a class, and what a Java caller sees when it calls `setStatus`. Explain it in your own words.",
  "answer": "`log.recorded(\"NEW\")` returns a delegate provider, so while the object is being constructed the compiler calls its `provideDelegate` with the property's `KProperty`, and stores the `Recorded` it returns in a hidden private field called `status$delegate`. The class also gets one static array, `$$delegatedProperties`, holding a `KProperty` for each delegated property. The getter `getStatus()` loads the delegate and the matching `KProperty` and calls `getValue`, then casts the result to `String`. The setter calls `setValue(this, property, value)`, which is where `Recorded` compares the old and new value and writes a change to the log. A Java caller sees nothing special: just a public `setStatus(String)` method. It can't tell there's a delegate behind it, but the audit still happens, because the logic lives in the setter the compiler generated."
 },
 "deeper": {
  "minutes": 8,
  "body": "Delegating to another property is the one case worth knowing that has no `$delegate` field at all. It is useful when you rename a property and need the old name for a while:\n\n```java\n// Java keeps the old accessor by hand and marks it deprecated\npublic long getAmountMinor() { return amountMinor; }\n@Deprecated public long getAmount() { return amountMinor; }\n```\n\n```kotlin\nclass Payment {\n    var amountMinor: Long = 0\n\n    @Deprecated(\"Use amountMinor\", ReplaceWith(\"amountMinor\"))\n    var amount: Long by this::amountMinor\n}\n```\n\n`javap -p` on that class shows `getAmount` and `setAmount`, a static helper `getAmount$delegate(Payment)`, and no `amount$delegate` field: the compiler reads and writes `amountMinor` directly. The IDE offers the `ReplaceWith` fix at every call site, so the rename can finish over a few releases.\n\nThe other cases without a field, from the docs: a delegate that is a named `object`, `this`, a constant expression or an enum entry, and \"a final val property with a backing field and a default getter in the same module\". Everything else pays for one delegate object per property per instance.\n\nOne more design note on class delegation. It composes well with the patterns track's decorators because the delegate never calls back into your class. With inheritance, `HashSet.addAll` calls `add`, so an override of `add` sees every element. With `by`, `addAll` goes to the inner set, and your `add` override is skipped. Neither is wrong, but only the `by` version is stable across JDK updates, because it doesn't depend on how the parent class happens to be written."
 },
 "sources": [
  {"title": "Delegation (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegation.html"},
  {"title": "Delegated properties (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html"},
  {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"}
 ]
}
out = ROOT / "content/lessons/kt-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
