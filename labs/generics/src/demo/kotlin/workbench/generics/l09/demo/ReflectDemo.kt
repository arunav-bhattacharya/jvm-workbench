package workbench.generics.l09.demo

import kotlin.reflect.full.createInstance
import kotlin.reflect.typeOf

/** A Kotlin object: exactly one instance. */
object Origin { override fun toString() = "Origin" }
class NoArg { override fun toString() = "NoArg()" }

private fun attempt(label: String, block: () -> Any?) {
    val result = try {
        block().toString()
    } catch (e: Throwable) {                        // KotlinReflectionNotSupportedError is an Error
        "${e::class.java.simpleName}: ${e.message?.substringBefore(". ")}"
    }
    println("%-24s %s".format(label, result))
}

/**
 * Run it twice:
 *   ./gradlew :generics:demo -Pmain=workbench.generics.l09.demo.ReflectDemoKt            (without kotlin-reflect)
 *   ./gradlew :generics:demo -Pmain=workbench.generics.l09.demo.ReflectDemoKt -Preflect  (with it)
 */
fun main() {
    println("-- standard library only")
    attempt("simpleName") { PaymentEvent::class.simpleName }
    attempt("isInstance") { CardAuthorized::class.isInstance(CardAuthorized("pay_1", 1)) }
    attempt("== and .java") { CardAuthorized::class.java == CardAuthorized("pay_1", 1).javaClass }
    attempt("typeOf arguments") { typeOf<List<String>>().arguments.size }
    attempt("toString()") { String::class }
    println("-- needs kotlin-reflect")
    attempt("objectInstance") { Origin::class.objectInstance }
    attempt("sealedSubclasses") { PaymentEvent::class.sealedSubclasses.map { it.simpleName } }
    attempt("isData") { CardAuthorized::class.isData }
    attempt("members") { CardAuthorized::class.members.map { it.name }.sorted() }
    attempt("createInstance()") { NoArg::class.createInstance() }
}
