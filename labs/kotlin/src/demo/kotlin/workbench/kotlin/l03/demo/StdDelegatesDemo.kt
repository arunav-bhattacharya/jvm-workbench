package workbench.kotlin.l03.demo

import kotlin.properties.Delegates
import kotlin.properties.PropertyDelegateProvider
import kotlin.properties.ReadOnlyProperty

class PrintRequest {
    // observable: the handler runs after the assignment
    var owner: String by Delegates.observable("<none>") { property, old, new ->
        println("${property.name}: $old -> $new")
    }

    // vetoable: the handler runs before the assignment; false keeps the old value
    var copies: Int by Delegates.vetoable(1) { _, _, new -> new <= 100 }
}

class PrinterConfig(settings: Map<String, Any?>) {
    val host: String by settings                  // reads settings["host"]
    val port: Int by settings                     // reads settings["port"]
}

/** provideDelegate runs once per property, while the object is built: validation happens right away. */
fun requiredSetting(): PropertyDelegateProvider<Any?, ReadOnlyProperty<Any?, String>> =
    PropertyDelegateProvider { _, property ->
        println("binding ${property.name}")
        ReadOnlyProperty { _, _ -> "value of ${property.name}" }
    }

class ShopSettings {
    val printerHost: String by requiredSetting()
}

fun main() {
    val request = PrintRequest()
    request.owner = "alice"
    request.owner = "bob"
    request.copies = 500
    println("copies after veto: ${request.copies}")
    request.copies = 50
    println("copies after ok: ${request.copies}")

    val config = PrinterConfig(mapOf("host" to "laser-1.local"))
    println("host = ${config.host}")
    try {
        println("port = ${config.port}")
    } catch (e: NoSuchElementException) {
        println("port failed on access: ${e.message}")
    }

    println("building ShopSettings...")
    val s = ShopSettings()
    println("built; printerHost = ${s.printerHost}")
}
