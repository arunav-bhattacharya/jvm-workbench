package workbench.generics.l09.demo

import kotlin.reflect.full.createInstance
import kotlin.reflect.typeOf

/** A Kotlin object: exactly one instance. The shop has one storeroom. */
object Storeroom { override fun toString() = "Storeroom" }
class PaperBag { override fun toString() = "PaperBag()" }

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
    attempt("simpleName") { Fruit::class.simpleName }
    attempt("isInstance") { Apple::class.isInstance(Apple("Gala", 180)) }
    attempt("== and .java") { Apple::class.java == Apple("Gala", 180).javaClass }
    attempt("typeOf arguments") { typeOf<List<String>>().arguments.size }
    attempt("toString()") { String::class }
    println("-- needs kotlin-reflect")
    attempt("objectInstance") { Storeroom::class.objectInstance }
    attempt("sealedSubclasses") { Fruit::class.sealedSubclasses.map { it.simpleName } }
    attempt("isData") { Apple::class.isData }
    attempt("members") { Apple::class.members.map { it.name }.sorted() }
    attempt("createInstance()") { PaperBag::class.createInstance() }
}
