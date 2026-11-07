package workbench.kotlin.l03.demo

import kotlin.properties.Delegates
import kotlin.properties.PropertyDelegateProvider
import kotlin.properties.ReadOnlyProperty

class Payout {
    // observable: the handler runs after the assignment
    var owner: String by Delegates.observable("<none>") { property, old, new ->
        println("${property.name}: $old -> $new")
    }

    // vetoable: the handler runs before the assignment; false keeps the old value
    var limit: Int by Delegates.vetoable(100) { _, _, new -> new <= 100 }
}

class IssuerConfig(settings: Map<String, Any?>) {
    val host: String by settings                  // reads settings["host"]
    val port: Int by settings                     // reads settings["port"]
}

/** provideDelegate runs once per property, while the object is built: validation happens right away. */
fun requiredEnv(): PropertyDelegateProvider<Any?, ReadOnlyProperty<Any?, String>> =
    PropertyDelegateProvider { _, property ->
        println("binding ${property.name}")
        ReadOnlyProperty { _, _ -> "value of ${property.name}" }
    }

class Settings {
    val issuerUrl: String by requiredEnv()
}

fun main() {
    val p = Payout()
    p.owner = "alice"
    p.owner = "bob"
    p.limit = 500
    println("limit after veto: ${p.limit}")
    p.limit = 50
    println("limit after ok: ${p.limit}")

    val config = IssuerConfig(mapOf("host" to "issuer.example"))
    println("host = ${config.host}")
    try {
        println("port = ${config.port}")
    } catch (e: NoSuchElementException) {
        println("port failed on access: ${e.message}")
    }

    println("building Settings...")
    val s = Settings()
    println("built; issuerUrl = ${s.issuerUrl}")
}
