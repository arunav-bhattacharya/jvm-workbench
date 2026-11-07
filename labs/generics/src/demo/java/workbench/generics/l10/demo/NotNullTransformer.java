package workbench.generics.l10.demo;

import org.jetbrains.annotations.NotNull;

/** A Java interface with nullability annotations. Kotlin reads @NotNull T as "T & Any". */
public interface NotNullTransformer<T> {
    @NotNull T transform(@NotNull T value);
}
