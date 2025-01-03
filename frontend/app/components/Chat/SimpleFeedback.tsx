import React, { useState } from 'react'
import VerbaButton from "../Navigation/VerbaButton";
import { ThumbsUp, ThumbsDown, X, MessageSquare } from 'lucide-react';
import { IconType } from 'react-icons';

interface SimpleFeedbackProps {
  runId: string;
  onSubmit: (runId: string, feedbackType: string, additionalFeedback: string) => void;
}

export default function SimpleFeedback({ runId, onSubmit }: SimpleFeedbackProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [feedbackType, setFeedbackType] = useState<string | null>(null)
  const [additionalFeedback, setAdditionalFeedback] = useState('')

  const handleFeedback = (type: string) => {
    if (type === 'positive') {
      onSubmit(runId, type, '');
      resetFeedbackState();
    } else {
      setFeedbackType('negative')
    }
  }

  const handleSubmitFeedback = () => {
    console.log('Submitting feedback:', { feedbackType, additionalFeedback });
    if (feedbackType) {
      onSubmit(runId, feedbackType, additionalFeedback);
    }
    resetFeedbackState();
  }

  const resetFeedbackState = () => {
    setIsOpen(false);
    setFeedbackType(null);
    setAdditionalFeedback('');
  }

  return (
    <>
      <VerbaButton
        title="Feedback"
        Icon={MessageSquare as IconType}
        onClick={() => setIsOpen(true)}
        selected={false}
        disabled={!runId}
      />
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div 
            className="bg-bg-alt-verba rounded-lg p-6 w-96 relative"
            role="dialog"
            aria-modal="true"
            aria-labelledby="feedback-title"
          >
            <VerbaButton
              Icon={X as IconType}
              onClick={resetFeedbackState}
              className="absolute right-2 top-2"
              selected={false}
              disabled={false}
            />
            <h2 
              id="feedback-title"
              className="text-xl font-bold mb-4"
            >
              {feedbackType === null ? "Was this helpful?" : "What could we improve?"}
            </h2>
            
            {feedbackType === null ? (
              <div className="flex justify-center space-x-4 mt-4">
                <VerbaButton
                  title="Yes"
                  Icon={ThumbsUp as IconType}
                  onClick={() => handleFeedback('positive')}
                  selected={false}
                  disabled={false}
                  selected_color="bg-success-verba"
                />
                <VerbaButton
                  title="No"
                  Icon={ThumbsDown as IconType}
                  onClick={() => handleFeedback('negative')}
                  selected={false}
                  disabled={false}
                  selected_color="bg-error-verba"
                />
              </div>
            ) : (
              <>
                <textarea 
                  placeholder="Please provide your feedback..." 
                  value={additionalFeedback}
                  onChange={(e) => {
                    console.log('Setting feedback:', e.target.value);
                    setAdditionalFeedback(e.target.value);
                  }}
                  className="w-full p-2 rounded bg-bg-verba text-text-verba mt-4"
                />
                <VerbaButton
                  title="Submit Feedback"
                  onClick={handleSubmitFeedback}
                  className="w-full mt-4"
                  selected={false}
                  disabled={false}
                  selected_color="bg-primary-verba"
                />
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}