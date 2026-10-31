package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Seat booking for a small concert venue. Each seat may be sold once.
 *
 * <p>The map is a {@link ConcurrentHashMap}, so each single call on it is thread-safe.
 * The booking still double-sells seats under load. Fix {@link #book} so a seat is
 * sold at most once, without locking the whole object.
 */
public class SeatMap {
    private final Map<Integer, String> owners = new ConcurrentHashMap<>();

    /** Returns true if {@code passenger} got {@code seat}, false if it was already taken. */
    public boolean book(int seat, String passenger) {
        if (!owners.containsKey(seat)) {   // check
            priceTheSeat();                // a slow step between check and act
            owners.put(seat, passenger);   // act
            return true;
        }
        return false;
    }

    /** Who holds {@code seat}, or null. */
    public String ownerOf(int seat) {
        return owners.get(seat);
    }

    // stands in for a call to a pricing service; it widens the gap between check and act
    private static void priceTheSeat() {
        for (int i = 0; i < 300; i++) Thread.onSpinWait();
    }
}
