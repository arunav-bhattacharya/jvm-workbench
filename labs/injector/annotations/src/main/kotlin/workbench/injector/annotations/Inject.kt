package workbench.injector.annotations

/**
 * The capstone's sticky note for "the plan may build this class". Put it on the constructor the plan should
 * call (`class Driver @Inject constructor(val route: Route)`) or on the class itself, which means its primary
 * constructor (`@Inject class Driver(val route: Route)`). Each constructor parameter is something the class
 * needs, a dependency, and the plan hands it in.
 *
 * RUNTIME retention, like `javax.inject.Inject`: the KSP processors would be happy with SOURCE, but the
 * reflection containers in the cap5 demos read these notes while the program runs.
 */
@Target(AnnotationTarget.CLASS, AnnotationTarget.CONSTRUCTOR)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Inject
