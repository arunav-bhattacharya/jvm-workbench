package workbench.injector.annotations.smoke

/**
 * Smoke example (keep or delete): put it on a class with a constructor that takes no parameters, and the smoke
 * processor generates `object <ClassName>Factory { fun create(): <ClassName> }` next to it.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Factory
