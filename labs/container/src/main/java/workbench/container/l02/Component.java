package workbench.container.l02;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Marks a class the container may create and inject. RUNTIME retention is what makes the
 * annotation visible to reflection: with the default (CLASS) the scanner would never see it.
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Component {
    Scope scope() default Scope.SINGLETON;
}
