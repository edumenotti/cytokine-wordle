import { Cell } from '../grid/Cell'
import { BaseModal } from './BaseModal'

type Props = {
  isOpen: boolean
  handleClose: () => void
}

export const InfoModal = ({ isOpen, handleClose }: Props) => {
  return (
    <BaseModal title="How to play" isOpen={isOpen} handleClose={handleClose}>
      <p className="text-sm text-gray-500 dark:text-gray-300">
        Wordle but for cytokines genes!
      </p>
      <p className="text-sm text-gray-500 dark:text-gray-300 focus:outline-none">
        Use{' '}
        <a
          className="text-sm text-blue-500 dark:text-blue-300"
          target="_blank"
          rel="noreferrer"
          href="https://www.genenames.org/"
        >
          genenames.org
        </a>{' '}
        to find suggestions.
      </p>
      <p className="text-sm text-gray-500 dark:text-gray-300">
        Genes with less than 5 characters are extended with "-".
      </p>
      <div className="flex justify-center mb-1 mt-4">
        <Cell isRevealing={true} isCompleted={true} value="C" status="absent" />
        <Cell isRevealing={true} isCompleted={true} value="C" status="absent" />
        <Cell 
	  isRevealing={true}
          isCompleted={true}
          value="L"
          status="present"
	/>
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="3"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="-"
          status="correct"
        />
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-300">
        The symbol L is in the gene name but in wrong spot. "-" and "3" are in the gene name and in the correct spot.
      </p>

      <div className="flex justify-center mb-1 mt-4">
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="I"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="L"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="3"
          status="present" 
	/>
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="1"
          status="present"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="-"
          status="correct"
        />
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-300">
        The symbols I and L are also the gene name in the correct spot. We discovered that "1" is in the gene name in the wrong spot.
      </p>

      <div className="flex justify-center mb-1 mt-4">
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="I"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="L"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="1"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="3"
          status="correct"
        />
        <Cell
          isRevealing={true}
          isCompleted={true}
          value="-"
          status="correct"
        />
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-300">
        By swaping 1 and 3, we discover that the gene is IL13!
      </p>

      <p className="mt-6 italic text-sm text-gray-500 dark:text-gray-300">
        Check the open source code{' '}
        <a
          href="https://github.com/lubianat/react-wordle"
          className="underline font-bold"
        >
          here
        </a>{' '}
      </p>
    </BaseModal>
  )
}
