package workbench.ksp.l01

import java.lang.reflect.Modifier
import workbench.ksp.annotations.Inventory

// Part 2: the same card, worked out while the program runs. Reflection opens the object at run time: it asks
// the class for its annotations and its fields, then reads each field's value. No card is written by hand.

/**
 * The inventory card of [thing], by reflection: its class's simple name, a colon, then name=value for each
 * instance field, in the order `getDeclaredFields()` returns them (static and synthetic fields skipped).
 * Throws IllegalArgumentException("<Name> has no @Inventory note") when the class doesn't carry @Inventory.
 *
 * Tools: `thing.javaClass`, `isAnnotationPresent(Inventory::class.java)`, `declaredFields`,
 * `Modifier.isStatic(field.modifiers)`, `field.isSynthetic`, `field.isAccessible = true`, `field.get(thing)`.
 */
fun reflectionCard(thing: Any): String =
    TODO("check for @Inventory, then build the card from the object's fields")
