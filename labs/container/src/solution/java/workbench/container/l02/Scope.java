package workbench.container.l02;

/** How many instances of a component the container makes. */
public enum Scope {
    /** One instance for the whole container, created on first use. */
    SINGLETON,
    /** A new instance every time someone asks for one or needs one injected. */
    PROTOTYPE
}
