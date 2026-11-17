package workbench.container.l02.demo

import workbench.container.l02.Container
import workbench.container.l02.ContainerException
import workbench.container.l02.demo.app.BookingClient
import workbench.container.l02.demo.app.FlakyBooking
import workbench.container.l02.demo.app.BookingScript
import java.lang.reflect.InvocationHandler
import java.lang.reflect.Proxy

// The container's JDK proxy next to one whose handler forwards every method, equals included.
fun main() {
    val c = Container(listOf(BookingScript::class.java, FlakyBooking::class.java))
    val booking = c.get(BookingClient::class.java)
    println("bean class: ${booking.javaClass.name} implements ${booking.javaClass.interfaces.map { it.simpleName }}")
    report("container's handler", booking)

    val target = FlakyBooking(BookingScript())
    val forwardAll = InvocationHandler { _, method, a -> method.invoke(target, *(a ?: emptyArray())) }   // equals too
    report("forward everything", Proxy.newProxyInstance(
        BookingClient::class.java.classLoader, arrayOf(BookingClient::class.java), forwardAll) as BookingClient)

    try {
        c.get(FlakyBooking::class.java)
    } catch (e: ContainerException) {
        println("get(FlakyBooking::class.java): ${e.message}")
    }
}

private fun report(name: String, p: BookingClient) {
    val listeners = mutableListOf(p)
    println("%-20s p.equals(p)=%s  listeners.remove(p)=%s  hashCode is identity=%s".format(
        name, p.equals(p), listeners.remove(p), p.hashCode() == System.identityHashCode(p)))
}
