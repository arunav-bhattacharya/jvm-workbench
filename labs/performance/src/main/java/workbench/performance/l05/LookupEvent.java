package workbench.performance.l05;

import jdk.jfr.Event;

/**
 * TODO: turn this into a JFR event that records one document lookup.
 *
 * <ul>
 *   <li>Name it {@code workbench.Lookup} with {@code @Name}, so recordings and tools can find it.</li>
 *   <li>Give it a {@code @Label} and put it in a {@code @Category} that includes {@code "Reports"}.</li>
 *   <li>Fields: {@code String shelf}, {@code String title}, {@code boolean found}, each with a {@code @Label}.</li>
 * </ul>
 * The event's own duration (begin/end) will cover the call to the document store.
 */
public class LookupEvent extends Event {
}
