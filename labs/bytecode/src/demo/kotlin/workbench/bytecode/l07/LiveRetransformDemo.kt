package workbench.bytecode.l07

import net.bytebuddy.agent.ByteBuddyAgent
import net.bytebuddy.agent.builder.AgentBuilder
import net.bytebuddy.asm.Advice
import net.bytebuddy.matcher.ElementMatchers.`is`
import net.bytebuddy.matcher.ElementMatchers.named

/** Final, like every Kotlin class without `open`: lesson 5's subclass proxies couldn't touch it. */
class KFxClock {
    fun now() = "tick"
}

object KTimingAdvice {
    @JvmStatic
    @Advice.OnMethodEnter
    fun enter(): Long = System.nanoTime()        // copied to the start of now()

    @JvmStatic
    @Advice.OnMethodExit(onThrowable = Throwable::class)
    fun exit(@Advice.Origin("#t.#m") where: String, @Advice.Enter t0: Long) {
        println("  [advice] $where took ${System.nanoTime() - t0} ns")
    }
}

/** Attach an agent to this running JVM and change a loaded class under a live object. */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {                     // -Pargs=allowed or -Pargs=blocked
        relaunch(args[0])
        return
    }
    val clock = KFxClock()
    println("before: ${clock.now()}")

    val inst = ByteBuddyAgent.install()          // self-attach: JEP 451 warns unless allowed
    println("retransform supported: ${inst.isRetransformClassesSupported}")
    AgentBuilder.Default()
        .disableClassFormatChanges()
        .with(AgentBuilder.RedefinitionStrategy.RETRANSFORMATION)
        .type(`is`(KFxClock::class.java))
        .transform { builder, _, _, _, _ -> builder.visit(Advice.to(KTimingAdvice::class.java).on(named("now"))) }
        .installOn(inst)

    println("after:  ${clock.now()}   (the same object, no restart)")
}

/** Runs this demo again in a child JVM with dynamic agent loading explicitly allowed or blocked. */
private fun relaunch(mode: String) {
    val flag = if (mode == "blocked") "-XX:-EnableDynamicAgentLoading" else "-XX:+EnableDynamicAgentLoading"
    val java = ProcessHandle.current().info().command().orElse("java")
    val child = ProcessBuilder(java, flag, "-cp", System.getProperty("java.class.path"), "workbench.bytecode.l07.LiveRetransformDemoKt")
        .redirectErrorStream(true)
        .start()
    println("child JVM with $flag:")
    child.inputStream.transferTo(System.out)
    println("child exited with ${child.waitFor()}")
}
