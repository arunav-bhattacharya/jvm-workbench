package workbench.container.l02.demo

import workbench.container.l02.Container
import workbench.container.l02.ContainerException
import workbench.container.l02.demo.app.CardIssuerClient
import workbench.container.l02.demo.app.FlakyIssuer
import workbench.container.l02.demo.app.IssuerScript
import java.lang.reflect.InvocationHandler
import java.lang.reflect.Proxy

// The container's JDK proxy next to one whose handler forwards every method, equals included.
fun main() {
    val c = Container(listOf(IssuerScript::class.java, FlakyIssuer::class.java))
    val issuer = c.get(CardIssuerClient::class.java)
    println("bean class: ${issuer.javaClass.name} implements ${issuer.javaClass.interfaces.map { it.simpleName }}")
    report("container's handler", issuer)

    val target = FlakyIssuer(IssuerScript())
    val forwardAll = InvocationHandler { _, method, a -> method.invoke(target, *(a ?: emptyArray())) }   // equals too
    report("forward everything", Proxy.newProxyInstance(
        CardIssuerClient::class.java.classLoader, arrayOf(CardIssuerClient::class.java), forwardAll) as CardIssuerClient)

    try {
        c.get(FlakyIssuer::class.java)
    } catch (e: ContainerException) {
        println("get(FlakyIssuer::class.java): ${e.message}")
    }
}

private fun report(name: String, p: CardIssuerClient) {
    val listeners = mutableListOf(p)
    println("%-20s p.equals(p)=%s  listeners.remove(p)=%s  hashCode is identity=%s".format(
        name, p.equals(p), listeners.remove(p), p.hashCode() == System.identityHashCode(p)))
}
