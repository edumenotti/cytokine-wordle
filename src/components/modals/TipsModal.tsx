import { GameStats } from '../../lib/localStorage'
import { solution } from '../../lib/words'
import { BaseModal } from './BaseModal'
import data from '../../constants/tiplist.json'
import wikipediaPages from '../../constants/wikipedialist.json'
import { TIPS_TITLE } from '../../constants/strings'

type Props = {
  isOpen: boolean
  handleClose: () => void
  guesses: string[]
  gameStats: GameStats
  isGameLost: boolean
  isGameWon: boolean
  isHardMode: boolean
  isDarkMode: boolean
  isHighContrastMode: boolean
}

export const TipsModal = ({ isOpen, handleClose }: Props) => {
  let gene_cards = `https://www.genecards.org/cgi-bin/carddisp.pl?gene=${solution.replaceAll(
    '-',
    ''
  )}`

  let tip = data[solution]
  let wikipediaPage = wikipediaPages[solution]

  return (
    <BaseModal title={TIPS_TITLE} isOpen={isOpen} handleClose={handleClose}>
      <br />
      <p className="text-slate-900 dark:text-slate-100">
        The cytokine of the day {tip}
      </p>
      <br />
      <p className="text-lg font-semibold text-slate-700 dark:text-slate-300">
        Spoilers:
      </p>
      <br />
      <a
        className="text-lg font-medium text-green-700 dark:text-green-300 hover:text-yellow-700 dark:hover:text-yellow-300"
        target="_blank"
        rel="noreferrer"
        href={wikipediaPage}
      >
        {' '}
        Read about the cytokine of the day on Wikipedia
      </a>
      <br />
      <br />
      <a
        className="text-lg leading-6 font-medium text-green-700 dark:text-green-300 hover:text-yellow-700 dark:hover:text-yellow-300"
        target="_blank"
        rel="noreferrer"
        href={gene_cards}
      >
        {' '}
        Read about the cytokine of the day on GeneCards
      </a>
      <br />
    </BaseModal>
  )
}
