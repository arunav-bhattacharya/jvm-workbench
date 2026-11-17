package workbench.container.l02.demo

import workbench.container.l02.Container
import workbench.container.l02.demo.app.BookingClient
import workbench.container.l02.demo.app.FlakyBooking
import workbench.container.l02.demo.app.BookingScript
import workbench.container.l02.demo.app.BookingUnavailableException
import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.lang.reflect.Proxy

// reserveAndConfirm, with one confirmation timing out: what does the booking service see?
fun main() {
    val c = Container(listOf(BookingScript::class.java, FlakyBooking::class.java))
    val script = c.get(BookingScript::class.java)
    script.confirmFailures.set(1)
    val result = c.get(BookingClient::class.java).reserveAndConfirm("C12", 12_000)
    println("container's proxy:  $result, booking service saw ${script.seen}")
    println("  timed calls: ${c.callLog().names()}")

    val naiveScript = BookingScript().apply { confirmFailures.set(1) }
    val target = FlakyBooking(naiveScript)
    val retryEverything = InvocationHandler { _, method, a -> callWithRetry(target, method, a) }   // any method, defaults too
    val naive = Proxy.newProxyInstance(BookingClient::class.java.classLoader,
        arrayOf(BookingClient::class.java), retryEverything) as BookingClient
    println("retry the shell:    ${naive.reserveAndConfirm("C12", 12_000)}, booking service saw ${naiveScript.seen}")
}

private fun callWithRetry(target: Any, method: Method, a: Array<Any?>?, attempt: Int = 1): Any? =
    try {
        method.invoke(target, *(a ?: emptyArray()))                       // the default body runs on the target
    } catch (e: InvocationTargetException) {
        if (attempt == 3 || e.cause !is BookingUnavailableException) throw e.cause!!
        callWithRetry(target, method, a, attempt + 1)
    }
