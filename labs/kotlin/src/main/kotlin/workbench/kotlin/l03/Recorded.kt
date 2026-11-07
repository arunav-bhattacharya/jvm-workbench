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

/**
 * A property delegate that holds a value and writes a [Change] to [log] whenever the value really changes.
 *
 * TODO 1: getValue returns the current value.
 * TODO 2: setValue adds Change(property.name, old, new) to log.changes, but only if the new value
 * differs from the old one (==), and then stores it.
 */
class Recorded<T>(private var value: T, private val log: ChangeLog) : ReadWriteProperty<Any?, T> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): T = TODO("return the value")

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        TODO("record a real change, then store the value")
    }
}

/**
 * Use as `var status: String by log.recorded("NEW")`.
 *
 * TODO 3: return a PropertyDelegateProvider { thisRef, property -> ... }. The compiler calls it once per
 * property while the owning object is constructed. In it:
 *  - if property.name is already in tracked, throw IllegalStateException (use check)
 *  - add property.name to tracked
 *  - return a new Recorded(initial, this)
 */
fun <T> ChangeLog.recorded(initial: T): PropertyDelegateProvider<Any?, Recorded<T>> =
    TODO("PropertyDelegateProvider { _, property -> ... }")
