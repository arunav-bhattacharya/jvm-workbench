package workbench.kotlin.l03

import kotlin.properties.PropertyDelegateProvider
import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty

/** One change to one property. */
data class Change(val property: String, val old: Any?, val new: Any?)

/** Collects the changes of every property created with [recorded]. */
class ChangeLog {
    /** Property names, registered when the owning object is built. */
    val tracked = mutableListOf<String>()
    val changes = mutableListOf<Change>()
}

/** A property delegate that holds a value and writes a [Change] to [log] whenever the value really changes. */
class Recorded<T>(private var value: T, private val log: ChangeLog) : ReadWriteProperty<Any?, T> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        // property.name comes from the KProperty the compiler passes in ($$delegatedProperties[i])
        if (value != this.value) log.changes += Change(property.name, this.value, value)
        this.value = value
    }
}

/**
 * Use as `var status: String by log.recorded("NEW")`.
 *
 * The compiler calls provideDelegate once per property, while the owning object is constructed,
 * so the name check below runs before anybody reads or writes the property.
 */
fun <T> ChangeLog.recorded(initial: T): PropertyDelegateProvider<Any?, Recorded<T>> =
    PropertyDelegateProvider { _, property ->
        check(property.name !in tracked) { "${property.name} is already tracked by this log" }
        tracked += property.name
        Recorded(initial, this)
    }
