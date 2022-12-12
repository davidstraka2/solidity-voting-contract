// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

import "./IVoteD21.sol";

// UC1 - Everyone can register a subject (e.g. political party)
// UC2 - Everyone can list registered subjects
// UC3 - Everyone can see the subject’s results
// UC4 - Only the owner can add eligible voters
// UC5 - Every voter has 2 positive and 1 negative vote
// UC6 - Voter can not give more than 1 vote to the same subject
// UC7 - Negative vote can be used only after 2 positive votes
// UC8 - Voting ends after 7 days from the contract deployment
contract D21 is IVoteD21 {
    error AllPositiveVotesUsed();
    error AllVotesUsed();
    error AlreadyAddedSubject();
    error AlreadyAddedVoter();
    error MaxOneVotePerSubject();
    error NegativeOnlyAfterPositiveVotes();
    error UnknownSubject();
    error UnknownVoter();
    error VotingEnded();

    // (firstVote, secondVote):
    // (0, 0) => uninitialized
    // (1, 1) => 2 positive and 1 negative votes remaining
    // (>0, 0) => 1 positive and 1 negative votes remaining
    // (>0, >0) & !(1, 1) => 1 negative vote remaining
    // (0, >0) => no votes remaining
    struct Voter {
        address firstVote;
        address secondVote;
    }

    // !! IMPORTANT !!
    // Comment out the two immutable keywords below for Brownie testing coverage
    // Keep them UNcommented for anything else, especially for gas estimates
    // (see https://github.com/eth-brownie/brownie/issues/1087#issuecomment-879015051)
    uint256 immutable votingEndTime; // Seconds since epoch
    address immutable owner;
    address[] subjectsAddr;
    mapping(address => Voter) votersByAddr;
    mapping(address => Subject) subjectsByAddr;

    constructor() {
        owner = msg.sender;
        votingEndTime = block.timestamp + 604800; // +7 days in seconds
    }

    // Add a new subject into the voting system using the name
    function addSubject(string memory name) external {
        Subject memory subject = subjectsByAddr[msg.sender];
        if (
            subject.votes != 0 ||
            bytes(subject.name).length != 0
        ) {
            revert AlreadyAddedSubject();
        }
        subjectsAddr.push(msg.sender);
        subjectsByAddr[msg.sender] = Subject({
            name: name,
            votes: 0
        });
    }

    // Add a new voter into the voting system
    function addVoter(address addr) external {
        require(msg.sender == owner); // dev: OnlyOwner
        Voter memory voter = votersByAddr[addr];
        if (
            voter.firstVote != address(0) ||
            voter.secondVote != address(0)
        ) {
            revert AlreadyAddedVoter();
        }
        votersByAddr[addr] = Voter({
            firstVote: address(1),
            secondVote: address(1)
        });
    }

    // Get addresses of all registered subjects
    function getSubjects() external view returns(address[] memory) {
        return subjectsAddr;
    }

    // Get the subject details
    function getSubject(address addr) external view returns(Subject memory) {
        return subjectsByAddr[addr];
    }

    // Vote positive for the subject
    function votePositive(address addr) external {
        // Ensure voting hasn't ended
        if (block.timestamp >= votingEndTime)
            revert VotingEnded();
        // Ensure voter is registered
        Voter memory voter = votersByAddr[msg.sender];
        if (
            voter.firstVote == address(0) &&
            voter.secondVote == address(0)
        ) {
            revert UnknownVoter();
        }
        // Ensure subject is registered
        Subject memory subject = subjectsByAddr[addr];
        if (
            subject.votes == 0 &&
            bytes(subject.name).length == 0
        ) {
            revert UnknownSubject();
        }
        // First positive vote
        if (
            voter.firstVote == address(1) &&
            voter.secondVote == address(1)
        ) {
            voter.firstVote = addr;
            voter.secondVote = address(0);
        // Second positive vote
        } else if (
            voter.firstVote != address(0) &&
            voter.secondVote == address(0)
        ) {
            if (voter.firstVote == addr)
                revert MaxOneVotePerSubject();
            voter.secondVote = addr;
        // Prevent third positive vote
        } else {
            revert AllPositiveVotesUsed();
        }
        // Every valid positive vote
        votersByAddr[msg.sender] = voter;
        ++subjectsByAddr[addr].votes;
    }

    // Vote negative for the subject
    function voteNegative(address addr) external {
        // Ensure voting hasn't ended
        if (block.timestamp >= votingEndTime)
            revert VotingEnded();
        // Ensure voter is registered
        Voter memory voter = votersByAddr[msg.sender];
        if (
            voter.firstVote == address(0) &&
            voter.secondVote == address(0)
        ) {
            revert UnknownVoter();
        }
        // Ensure subject is registered
        Subject memory subject = subjectsByAddr[addr];
        if (
            subject.votes == 0 &&
            bytes(subject.name).length == 0
        ) {
            revert UnknownSubject();
        }
        // Negative vote
        if (
            voter.firstVote != voter.secondVote &&
            voter.firstVote != address(0) &&
            voter.secondVote != address(0)
        ) {
            if (
                voter.firstVote == addr ||
                voter.secondVote == addr
            ) {
                revert MaxOneVotePerSubject();
            }
            votersByAddr[msg.sender].firstVote = address(0);
            --subjectsByAddr[addr].votes;
        // Prevent second negative vote
        } else if (
            voter.firstVote == address(0) &&
            voter.secondVote != address(0)
        ) {
            revert AllVotesUsed();
        // Ensure negative vote follows positive votes
        } else {
            revert NegativeOnlyAfterPositiveVotes();
        }
    }

    // Get the remaining time to the voting end in seconds
    function getRemainingTime() external view returns(uint256) {
        if (block.timestamp < votingEndTime) {
            unchecked {
                return votingEndTime - block.timestamp;
            }
        }
        return 0;
    }

    struct StackItem {
        uint lo;
        uint hi;
    }

    // Get the voting results, sorted descending by votes
    function getResults() external view returns(Subject[] memory subjects) {
        // Fetch subjects from storage into an array
        uint subjectCount = subjectsAddr.length;
        subjects = new Subject[](subjectCount);
        for (uint i; i < subjectCount;) {
            subjects[i] = subjectsByAddr[subjectsAddr[i]];
            unchecked {
                ++i;
            }
        }
        if (subjectCount < 2)
            return subjects;
        // Iterative QuickSort using Lomuto's partition scheme
        StackItem[] memory stack = new StackItem[]((subjectCount >> 1) + 2);
        stack[1] = StackItem({lo: 0, hi: subjectCount - 1});
        uint stackSize = 1;
        StackItem memory it;
        while (stackSize != 0) {
            it = stack[stackSize];
            unchecked {
                --stackSize;
            }
            int pivot = subjects[it.hi].votes;
            uint i = it.lo;
            for (uint j = it.lo; j < it.hi;) {
                if (subjects[j].votes > pivot) {
                    (subjects[i], subjects[j]) = (subjects[j], subjects[i]);
                    unchecked {
                        ++i;
                    }
                }
                unchecked {
                    ++j;
                }
            }
            (subjects[i], subjects[it.hi]) = (subjects[it.hi], subjects[i]);
            uint partIdx = i;
            if (partIdx > it.lo + 1) {
                unchecked {
                    ++stackSize;
                }
                stack[stackSize] = StackItem({lo: it.lo, hi: partIdx - 1});
            }
            if (partIdx + 1 < it.hi) {
                unchecked {
                    ++stackSize;
                }
                stack[stackSize] = StackItem({lo: partIdx + 1, hi: it.hi});
            }
        }
    }
}
