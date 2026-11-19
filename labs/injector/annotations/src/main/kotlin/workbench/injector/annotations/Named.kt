package workbench.injector.annotations

/**
 * A qualifier: a name that tells two bindings of the same type apart. A `@Provides @Named("highway")` function
 * answers a parameter declared `@Named("highway") route: Route`, and only that one.
 */
@Target(AnnotationTarget.VALUE_PARAMETER, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Named(val value: String)
