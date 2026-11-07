package workbench.container.l02.demo

import workbench.container.l02.Container
import workbench.container.l02.demo.app.CardIssuerClient
import workbench.container.l02.demo.app.FlakyIssuer
import workbench.container.l02.demo.app.IssuerScript
import workbench.container.l02.demo.app.IssuerUnavailableException
import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.lang.reflect.Proxy

// authorizeAndCapture, with one capture timing out: what does the issuer see?
fun main() {
    val c = Container(listOf(IssuerScript::class.java, FlakyIssuer::class.java))
    val script = c.get(IssuerScript::class.java)
    script.captureFailures.set(1)
    val result = c.get(CardIssuerClient::class.java).authorizeAndCapture("4111111111111111", 12_000)
    println("container's proxy:  $result, issuer saw ${script.seen}")
    println("  timed calls: ${c.callLog().names()}")

    val naiveScript = IssuerScript().apply { captureFailures.set(1) }
    val target = FlakyIssuer(naiveScript)
    val retryEverything = InvocationHandler { _, method, a -> callWithRetry(target, method, a) }   // any method, defaults too
    val naive = Proxy.newProxyInstance(CardIssuerClient::class.java.classLoader,
        arrayOf(CardIssuerClient::class.java), retryEverything) as CardIssuerClient
    println("retry the shell:    ${naive.authorizeAndCapture("4111111111111111", 12_000)}, issuer saw ${naiveScript.seen}")
}

private fun callWithRetry(target: Any, method: Method, a: Array<Any?>?, attempt: Int = 1): Any? =
    try {
        method.invoke(target, *(a ?: emptyArray()))                       // the default body runs on the target
    } catch (e: InvocationTargetException) {
        if (attempt == 3 || e.cause !is IssuerUnavailableException) throw e.cause!!
        callWithRetry(target, method, a, attempt + 1)
    }
