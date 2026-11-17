package workbench.bytecode.l04;

/** The theatre's seat booking desk, a service on another computer that the show program calls over the network. */
public interface SeatDesk {
    /** Holds a seat for {@code guest} at {@code show} and returns the hold's id, such as {@code "hold-hamlet"}. */
    String hold(String show, String guest) throws DeskUnavailableException;

    /** Confirms a hold and returns {@code "confirmed " + holdId}. */
    String confirm(String holdId) throws DeskUnavailableException;

    /** A default method: two calls on {@code this}. */
    default String holdAndConfirm(String show, String guest) throws DeskUnavailableException {
        return confirm(hold(show, guest));
    }

    /** Thrown when the desk can't be reached. Checked, and declared by every method. Worth a retry. */
    class DeskUnavailableException extends Exception {
        public DeskUnavailableException(String message) { super(message); }
    }

    /** The show has no seats left. Retrying won't add any. */
    class SoldOutException extends RuntimeException {
        public SoldOutException(String message) { super(message); }
    }
}
