package workbench.container.l02.demo

import net.bytebuddy.ByteBuddy
import workbench.container.l02.Component
import workbench.container.l02.Container
import workbench.container.l02.ContainerException
import workbench.container.l02.Timed
import java.lang.reflect.Modifier

// Two Kotlin classes with the same @Timed method. The build's all-open plugin opens only the second.
@Component
class KFinalPrices {
    @Timed
    fun feeCents(priceCents: Long) = (priceCents * 29 + 500) / 1000
}

@OpenForProxies
@Component
class KOpenedPrices {
    @Timed
    fun feeCents(priceCents: Long) = (priceCents * 29 + 500) / 1000
}

fun main() {
    for (type in listOf(KFinalPrices::class.java, KOpenedPrices::class.java)) {
        val fee = type.getMethod("feeCents", Long::class.java)
        println("${type.simpleName}: class final=${Modifier.isFinal(type.modifiers)}, feeCents final=${Modifier.isFinal(fee.modifiers)}")
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
        ByteBuddy().subclass(KFinalPrices::class.java).make()             // what you get without the check
    } catch (e: IllegalArgumentException) {
        println("Byte Buddy on its own: ${e.message}")
    }
}
