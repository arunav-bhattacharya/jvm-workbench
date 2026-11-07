package workbench.kotlin.l03.demo

import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty

/** A hand-written delegate: getValue and setValue are all the compiler needs. */
class Audited<T>(private var value: T) : ReadWriteProperty<Any?, T> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        println("  ${property.name}: ${this.value} -> $value")
        this.value = value
    }
}

class Order {
    var status: String by Audited("NEW")
    var amountMinor: Long by Audited(0L)
}

fun main() {
    val order = Order()
    order.status = "AUTHORIZED"
    order.amountMinor = 4_250
    println("status = ${order.status}, amountMinor = ${order.amountMinor}")
    println("fields the compiler generated:")
    Order::class.java.declaredFields.forEach { println("  ${it.type.simpleName} ${it.name}") }
}
