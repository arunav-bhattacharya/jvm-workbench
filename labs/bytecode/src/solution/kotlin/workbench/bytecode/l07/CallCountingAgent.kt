package workbench.bytecode.l07

import net.bytebuddy.agent.ByteBuddyAgent
import net.bytebuddy.agent.builder.AgentBuilder
import net.bytebuddy.asm.Advice
import net.bytebuddy.matcher.ElementMatchers.`is`
import net.bytebuddy.matcher.ElementMatchers.named
import java.lang.instrument.Instrumentation

fun interface Installed {
    fun uninstall()
}

object CallCountingAgent {
    // self-attach once; later calls return the same Instrumentation
    fun instrumentation(): Instrumentation = ByteBuddyAgent.install()

    fun countCalls(type: Class<*>, method: String): Installed {
        val transformer = AgentBuilder.Default()
            .disableClassFormatChanges()                                  // no new fields or methods: required to retransform
            .with(AgentBuilder.RedefinitionStrategy.RETRANSFORMATION)     // also rewrite classes that are already loaded
            .type(`is`(type))
            .transform { builder, _, _, _, _ ->
                builder.visit(Advice.to(CountingAdvice::class.java).on(named(method)))   // inline the advice into the body
            }
            .installOn(instrumentation())
        return Installed { transformer.reset(instrumentation(), AgentBuilder.RedefinitionStrategy.RETRANSFORMATION) }
    }
}

object CountingAdvice {
    @JvmStatic
    @Advice.OnMethodEnter                                                 // copied to the start of the method
    fun enter(@Advice.Origin("#t.#m") method: String) {                   // "#t.#m" = declaring type + method name
        CallCounts.hit(method)
    }
}
