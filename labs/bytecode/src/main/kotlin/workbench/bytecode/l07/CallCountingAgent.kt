package workbench.bytecode.l07

import java.lang.instrument.Instrumentation

/** Undoes an installed transformation. */
fun interface Installed {
    fun uninstall()
}

/**
 * Counts calls to one method of a class that is already loaded, in this running JVM, without
 * a restart and without a proxy.
 *
 * 1. [instrumentation]: attach Byte Buddy's agent to this JVM with `ByteBuddyAgent.install()`.
 * 2. [countCalls]: build an `AgentBuilder.Default()` that does `disableClassFormatChanges()`,
 *    uses `RedefinitionStrategy.RETRANSFORMATION`, matches `is(type)` and visits the method with
 *    `Advice.to(CountingAdvice::class.java).on(named(method))`. `installOn(instrumentation())`
 *    retransforms the loaded class. Return an [Installed] that calls
 *    `transformer.reset(instrumentation(), RedefinitionStrategy.RETRANSFORMATION)`.
 */
object CallCountingAgent {
    fun instrumentation(): Instrumentation = TODO("ByteBuddyAgent.install()")

    fun countCalls(type: Class<*>, method: String): Installed = TODO("AgentBuilder + Advice, then installOn")
}

/**
 * The advice. Byte Buddy copies the body of [enter] into the start of each matched method,
 * so it must be static (`@JvmStatic`) and may only call public code.
 */
object CountingAdvice {
    // TODO: annotate with @Advice.OnMethodEnter and take @Advice.Origin("#t.#m") method: String
    @JvmStatic
    fun enter(method: String) {
        CallCounts.hit(method)
    }
}
