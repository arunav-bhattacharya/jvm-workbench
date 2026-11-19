package workbench.ksp.annotations.l03

import kotlin.reflect.KClass

/** How the movers should treat a box (lesson 3 of the ksp track). */
enum class Care { NORMAL, GENTLE, UPRIGHT }

/**
 * Lesson 3: handling instructions for a class's boxes. Three kinds of argument, each with a default: an enum
 * ([care]), a Boolean ([stackable]) and a class ([packWith], the class these boxes travel with; the default,
 * `Any::class`, means they can go with anything). The lesson 3 processor prints them on the label, for example
 * `care=UPRIGHT, stackable=false, packWith=Lamp`.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Handling(
    val care: Care = Care.NORMAL,
    val stackable: Boolean = true,
    val packWith: KClass<*> = Any::class,
)
