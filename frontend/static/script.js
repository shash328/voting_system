// frontend_app/static/script.js

$(document).ready(function() {
    // Function to show notifications
    function showNotification(message, type) {
        const notification = $('#notification');
        notification.removeClass('success error').addClass(type).text(message).fadeIn();

        setTimeout(() => {
            notification.fadeOut();
        }, 5000);
    }

    // Submit vote
    $('#voteForm').submit(function(event) {
        event.preventDefault();
        const voter_id = $('#voter_id').val().trim();
        const candidate = $('#candidate').val().trim();

        if (!voter_id || !candidate) {
            showNotification('Please fill in both Voter ID and Candidate fields.', 'error');
            return;
        }

        const vote = { voter_id, candidate };

        $.ajax({
            url: '/submit_vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(vote),
            success: function(response) {
                showNotification(response.message, 'success');
                $('#voteForm')[0].reset();
                fetchChain();
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showNotification(response.message || 'An error occurred.', 'error');
            }
        });
    });

    // Fetch blockchain
    function fetchChain() {
        $.ajax({
            url: '/get_chain',
            type: 'GET',
            success: function(response) {
                const chain = response.chain;
                $('#blockchain').text(JSON.stringify(chain, null, 4));
            },
            error: function() {
                $('#blockchain').text('Failed to retrieve blockchain.');
            }
        });
    }

    // Refresh blockchain on button click
    $('#refreshChain').click(function() {
        fetchChain();
    });

    // Initial fetch
    fetchChain();
});
