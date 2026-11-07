package workbench.startup.l03.demo

import java.lang.reflect.InvocationHandler
import java.lang.reflect.Proxy

/** Builds two JDK dynamic proxies from the same two interfaces, in opposite orders. */
interface IssuerApi {
    fun authorize(paymentId: String): String
}

fun main() {
    val handler = InvocationHandler { _, method, a ->
        if (method.name == "authorize") "APPROVED ${a[0]}" else null
    }
    val loader = IssuerApi::class.java.classLoader

    val first = Proxy.newProxyInstance(loader, arrayOf(IssuerApi::class.java, AutoCloseable::class.java), handler)
    val second = Proxy.newProxyInstance(loader, arrayOf(AutoCloseable::class.java, IssuerApi::class.java), handler)
    val again = Proxy.newProxyInstance(loader, arrayOf(IssuerApi::class.java, AutoCloseable::class.java), handler)

    fun names(c: Class<*>) = c.interfaces.map { it.simpleName }
    println("first : ${first.javaClass.name} ${names(first.javaClass)}")
    println("second: ${second.javaClass.name} ${names(second.javaClass)}")
    println("same class for (A, B) and (B, A)? ${first.javaClass == second.javaClass}")
    println("same class for (A, B) twice?      ${first.javaClass == again.javaClass}")
    println((first as IssuerApi).authorize("pay_81"))
}
