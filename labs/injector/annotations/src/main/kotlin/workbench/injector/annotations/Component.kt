package workbench.injector.annotations

/**
 * Marks an interface that lists what the app asks the plan for, one function without parameters each, for
 * example `fun movingDay(): MovingDay`. The processor writes a class named `Generated<InterfaceName>` that
 * implements it and builds everything in the right order.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Component
