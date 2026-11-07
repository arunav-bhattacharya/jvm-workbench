# Track: kt, "Advanced Kotlin" (lab: labs/kotlin, package workbench.kotlin.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/advanced_kotlin.md" (real kotlinc 2.4.21 outputs and errors). The lab module
applies kotlinx.serialization (json 1.12.0), all-open (annotation workbench.kotlin.OpenForProxies)
and no-arg (annotation workbench.kotlin.NoArgEntity); declare those two annotation classes in
src/main and src/solution under package workbench.kotlin when kt-06 needs them. Labs in Kotlin; the
Java twin shows what Java sees (javap-style signatures, calling the Kotlin API from Java).
Link to gen-08 (reified), pat-03 (DSL builders), pat-05 (by delegation) without repeating them.

Lessons:
- kt-01 Inline functions: what inlining does, non-local returns, noinline, crossinline, inline
  properties, @PublishedApi, when not to inline. Lab: a retry helper with a crossinline block.
- kt-02 Value classes and what they compile to: @JvmInline, boxing rules, name mangling and @JvmName,
  calling from Java, Valhalla plans. Lab: Money and IdempotencyKey value classes with validation.
- kt-03 Delegation: class delegation (and its override trap), lazy and its three modes, observable,
  vetoable, map-backed properties, custom ReadWriteProperty, provideDelegate. Lab: an audited property delegate.
- kt-04 Type-safe DSLs: lambdas with receivers, @DslMarker, building a payment-request DSL, buildList.
- kt-05 Contracts and context parameters: callsInPlace and returns-implies, their status and opt-in;
  context parameters (preview since 2.2, status in 2.4, the compiler flag). Lab: a contract-backed
  require helper; context parameters only if the module can enable them without changing root files.
- kt-06 Compiler plugins: all-open and kotlin-spring, no-arg and kotlin-jpa, kotlinx.serialization of
  a sealed PaymentEvent hierarchy, KSP vs kapt in brief. Lab: serialization round trip and an
  all-open class that a Byte Buddy or JDK proxy can subclass.
