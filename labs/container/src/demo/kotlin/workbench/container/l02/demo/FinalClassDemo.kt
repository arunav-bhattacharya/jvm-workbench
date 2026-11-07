package workbench.container.l02.demo

import net.bytebuddy.ByteBuddy
import workbench.container.l02.Component
import workbench.container.l02.Container
import workbench.container.l02.ContainerException
import workbench.container.l02.Timed
import java.lang.reflect.Modifier

// Two Kotlin classes with the same @Timed method. The build's all-open plugin opens only the second.
@Component
class KFinalFees {
    @Timed
    fun feeMinor(amountMinor: Long) = (amountMinor * 29 + 500) / 1000
}

@OpenForProxies
@Component
class KOpenedFees {
    @Timed
    fun feeMinor(amountMinor: Long) = (amountMinor * 29 + 500) / 1000
}

fun main() {
    for (type in listOf(KFinalFees::class.java, KOpenedFees::class.java)) {
        val fee = type.getMethod("feeMinor", Long::class.java)
        println("${type.simpleName}: class final=${Modifier.isFinal(type.modifiers)}, feeMinor final=${Modifier.isFinal(fee.modifiers)}")
        try {
            val c = Container(listOf(type))
            val bean = c.get(type)
            fee.invoke(bean, 12_000L)
            println("  wired as ${bean.javaClass.simpleName}, timed calls ${c.callLog().names()}")
        } catch (e: ContainerException) {
            println("  refused: ${e.message}")
        }
    }
    try {
        ByteBuddy().subclass(KFinalFees::class.java).make()             // what you get without the check
    } catch (e: IllegalArgumentException) {
        println("Byte Buddy on its own: ${e.message}")
    }
}
